from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from openai import OpenAI
from scrapegraphai.graphs import SmartScraperGraph
from rest_framework.response import Response
from rest_framework.views import APIView
import os

class SaveEntityView(APIView):
    def get(self, request):
        url = request.GET.get('url')
        if not url:
            return Response({'error': 'URL parameter is required'}, status=400)

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get(url)
        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, 'html.parser')

        artist_details = []
        artist_elements = soup.select('.event-detail-artist')
        for element in artist_elements:
            artist_name = element.select_one('.subhead4').text.strip()
            artist_role = element.select_one('.subhead6').text.strip()
            artist_details.append({'artist_name': artist_name, 'artist_role': artist_role})

        program_names = [div.text.strip() for div in soup.select('.text-left .subhead4')]
        performance_times = [p.text.strip() for p in soup.select('.performance-card .body-text3')]

        date = soup.select_one('.performance-card .body-text3').text.split(',')[1].strip()
        time = soup.select_one('.performance-card .body-text3').text.split(',')[2].strip()
        auditorium = soup.select_one('.performance-card .subhead6 strong').text.strip()
        description = self.generate_description(artist_details, program_names, performance_times, date, time, auditorium)

        openai_key = os.getenv('OPENAI_API_KEY')

        graph_config = {
            "llm": {
                "api_key": openai_key,
                "model": "gpt-3.5-turbo",
            }
        }

        smart_scraper_graph = SmartScraperGraph(
            prompt="List me all the artists names artists role performance times auditorium",
            source=url,
            config=graph_config
        )
        openai_response = ''
        try:
            result = smart_scraper_graph.run()
            openai_response = result
        except Exception as e:
            openai_response = str(e)

        return Response({
            'artists': artist_details,
            'program_names': program_names,
            'performance_times': performance_times,
            'date': date,
            'time': time,
            'auditorium': auditorium,
            'description': description,
            'openai_response': openai_response,
        })

    def generate_description(self, artists, program_names, performance_times, date, time, auditorium):
        artists_text = '  '.join([f"{artist['artist_name']} - {artist['artist_role']}" for artist in artists])
        programs_text = '  '.join(program_names)
        template = f"The performance at {auditorium} on {date} at {time} features:{artists_text} The program includes: {programs_text} The performance time is {performance_times[0]}"
        return template
