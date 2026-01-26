from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_KEY = '8c6f67a3d7b3c594781593a6e15524c6ba71fe26'
HEADERS = {'User-Agent': 'MiAppComics/1.0'}

@app.route('/', methods=['GET', 'POST'])
def index():
    personaje = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        url = f"https://comicvine.gamespot.com/api/search/?api_key={API_KEY}&format=json&query={nombre}&resources=character&limit=1&field_list=name,real_name,deck,image,site_detail_url"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        if data['results']:
            personaje = data['results'][0]
            
    return render_template('index.html', personaje=personaje)

if __name__ == '__main__':
    app.run(debug=True)