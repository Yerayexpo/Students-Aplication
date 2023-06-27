from flask import Flask, request, jsonify
import openai
from sentiment_analysis_spanish import sentiment_analysis
from spanlp.palabrota import Palabrota
from flask import render_template, redirect, url_for, render_template_string
import requests
import folium
import googlemaps
from datetime import datetime
import polyline
import requests
from PIL import Image
import io
import base64
import os

app = Flask(__name__)
api_key= os.environ.get('google')
openai.api_key= os.environ.get('dalle')
gmaps = googlemaps.Client(key=api_key)

def obtener_rutas_cercanas(origen, destino):
    # Obtiene las direcciones y coordenadas geográficas del origen y el destino
    #origen_geocode = gmaps.geocode(origen)[0]
    destino_geocode = gmaps.geocode(destino)[0]
    #origen_coords = origen_geocode['geometry']['location']
    destino_coords = destino_geocode['geometry']['location']
    origen_coords = origen
    # Realiza la solicitud de direcciones a Google Maps utilizando transporte público
    now = datetime.now()
    directions_result = gmaps.directions(origen_coords, destino_coords, mode="transit", departure_time=now)

    # Obtiene las tres rutas públicas más cercanas
    rutas_cercanas = []
    for route in directions_result:
        rutas_cercanas.append({
            'distancia': route['legs'][0]['distance']['text'],
            'duracion': route['legs'][0]['duration']['text'],
            'pasos': [step for step in route['legs'][0]['steps'] if step['travel_mode'] == 'TRANSIT'],
            'polyline': route['overview_polyline']['points']
        })

    return rutas_cercanas[:3]

@app.route('/', methods=['GET', 'POST'])
def home():
    endpoints = [
        {
            'endpoint': '/mapa',
            'methods': ['GET'],
            'description': 'Obtener un mapa con rutas entre un origen y un destino, se proporciona el destino dentro de un json, el origen establecido es edem. Devuelve un codigo html con el mapa',
            'example': 'data = {"destino" : "Madrid"}',
            'url': 'https://desafio-api.onrender.com/mapa',
        },
        {
            'endpoint': '/generar',
            'methods': ['POST'],
            'description': 'Generar una imagen a partir de un prompt, se proporciona el prompt dentro de un json y devuelve una url',
            'example': 'data = {"prompt" : "un gato volando con capa"}',
            'url': 'https://desafio-api.onrender.com/generar',
        },
        {
            'endpoint': '/models/lenguaje',
            'methods': ['GET'],
            'description': 'Analizar el lenguaje de un mensaje y verificar si contiene alguna palabrota, se proporciona el mensaje dentro de un json y devuelve true en caso de bad lenaguaje o false',
            'example': 'data = {"message" : "Hola que tal estas"}',
            'url': 'https://desafio-api.onrender.com/models/lenguaje',
        },
    ]
    return render_template('index.html', endpoints=endpoints)

@app.route('/mapa', methods=['GET','POST'])
def obtener_mapa():
    # metodo http://localhost:5000/mapa/?destino=tu_destino
    origen =  {'lat' : 39.46219627815263, 'lng' : -0.3290567611975815}
    destino = request.json.get('destino')
    if not origen or not destino:
        return 'Debe proporcionar el origen y el destino en la URL'
    
    rutas = obtener_rutas_cercanas(origen, destino)
    mapa = folium.Map(location=[rutas[0]['pasos'][0]['start_location']['lat'], rutas[0]['pasos'][0]['start_location']['lng']], zoom_start=12)
    folium.Marker([rutas[0]['pasos'][0]['start_location']['lat'], rutas[0]['pasos'][0]['start_location']['lng']], popup=origen).add_to(mapa)

    for i, ruta in enumerate(rutas, start=1):
        decoded_polyline = polyline.decode(ruta['polyline'])
        locations = [[point[0], point[1]] for point in decoded_polyline]
        folium.PolyLine(locations, color='blue', weight=2.5, opacity=1).add_to(mapa)

    folium.Marker([rutas[0]['pasos'][-1]['end_location']['lat'], rutas[0]['pasos'][-1]['end_location']['lng']], popup=destino).add_to(mapa)

    mapa.save('mapa.html')

    with open('mapa.html', 'r') as f:
        contenido_mapa = f.read()

    return contenido_mapa

@app.route('/generar', methods=['POST'])
def generar():
    prompt1 = request.json.get('prompt')
    imagen_generada = generar_imagen(prompt1)
    return jsonify({'imagen_generada': imagen_generada})

def generar_imagen(prompt1):
    response = openai.Image.create(  
    prompt=prompt1,
    n=1,
    size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return image_url

@app.route('/models/lenguaje', methods=['GET', 'POST'])
def lenguaje():
    message = request.json.get('message')
    palabrota = Palabrota()
    lenguaje_result = palabrota.contains_palabrota(message)
    return jsonify({'lenguaje_result': lenguaje_result})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
