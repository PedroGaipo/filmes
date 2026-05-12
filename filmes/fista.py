from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
import requests
import urllib3
import pandas as pd
from werkzeug.utils import secure_filename
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
API_KEY = "c97e76ede1d73aa11a1e119a37741bc0"  # Sua chave

# Configuração para upload de arquivos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui'  # Para flash messages

# Criar pasta de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('DROP TABLE IF EXISTS filmes')
    conn.execute('''
        CREATE TABLE filmes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            diretor TEXT,
            nota REAL,
            comentario TEXT,
            categoria TEXT,
            poster_url TEXT,
            sinopse TEXT,
            elenco TEXT,
            ano TEXT
        )
    ''')
    # NOVA TABELA: lista_futuros (watchlist)
    conn.execute('DROP TABLE IF EXISTS lista_futuros')
    conn.execute('''
        CREATE TABLE lista_futuros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            diretor TEXT,
            genero TEXT,
            ator_principal TEXT,
            prioridade INTEGER DEFAULT 3,
            categoria TEXT,
            rotten_tomatoes TEXT,  -- Nota RT (string, ex: "85%")
            poster_url TEXT,
            sinopse TEXT,
            tmdb_id INTEGER UNIQUE  -- Pra evitar duplicatas
        )
    ''')
    conn.commit()
    conn.close()

def buscar_dados_tmdb(titulo_filme):
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": API_KEY, "query": titulo_filme, "language": "pt-BR"}
    try:
        response = requests.get(search_url, params=params, verify=False, timeout=10)
        if response.status_code != 200:
            print(f"DEBUG: Erro {response.status_code}")
            return None
        search_res = response.json()
        if not search_res.get('results'):
            return None
        filme_id = search_res['results'][0]['id']
        detail_url = f"https://api.themoviedb.org/3/movie/{filme_id}"
        detail_params = {"api_key": API_KEY, "language": "pt-BR", "append_to_response": "credits"}
        data = requests.get(detail_url, params=detail_params, verify=False, timeout=10).json()
        
        # CORRIGIDO: URL do poster
        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        
        elenco = ", ".join([ator['name'] for ator in data.get('credits', {}).get('cast', [])[:3]])
        diretor = next((m['name'] for m in data.get('credits', {}).get('crew', []) if m['job'] == 'Director'), "Desconhecido")
        genero = ", ".join([g['name'] for g in data.get('genres', [])[:3]]) if data.get('genres') else "N/A"
        ator_principal = elenco.split(", ")[0] if elenco else "N/A"
        
        # Nota Rotten Tomatoes (simulada/busca externa se quiser integrar depois)
        rotten_rt = "N/A"  # TODO: Integre OMDB ou RT API se precisar
        
        return {
            "titulo": data.get('title'),
            "diretor": diretor,
            "sinopse": data.get('overview'),
            "elenco": elenco,
            "poster_url": poster_url,
            "ano": data.get('release_date', '0000')[:4],
            "genero": genero,
            "ator_principal": ator_principal,
            "rotten_tomatoes": rotten_rt,
            "tmdb_id": filme_id
        }
    except Exception as e:
        print(f"ERRO NA BUSCA: {e}")
        return None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processar_excel_filmes(filepath):
    """Processa arquivo Excel e retorna lista de filmes para adicionar"""
    try:
        df = pd.read_excel(filepath)
        
        # Verificar se as colunas necessárias existem
        colunas_necessarias = ['titulo']
        colunas_opcionais = ['nota', 'categoria', 'comentario']
        
        if 'titulo' not in df.columns:
            return {'erro': 'A planilha deve ter uma coluna chamada "titulo"'}
        
        filmes_para_adicionar = []
        erros = []
        
        for index, row in df.iterrows():
            titulo = str(row.get('titulo', '')).strip()
            if not titulo:
                erros.append(f"Linha {index+2}: título vazio")
                continue
                
            # Buscar dados na TMDB
            dados = buscar_dados_tmdb(titulo)
            if not dados:
                erros.append(f"Linha {index+2}: filme '{titulo}' não encontrado na TMDB")
                continue
            
            # Usar dados da planilha se disponíveis, senão usar da TMDB
            nota = row.get('nota')
            if pd.notna(nota):
                try:
                    nota = float(nota)
                    nota = max(0, min(10, nota))  # Garantir que está entre 0 e 10
                except:
                    nota = None
            else:
                nota = None
                
            categoria = str(row.get('categoria', '')).strip() if pd.notna(row.get('categoria')) else ''
            comentario = str(row.get('comentario', '')).strip() if pd.notna(row.get('comentario')) else ''
            
            filmes_para_adicionar.append({
                'titulo': dados['titulo'],
                'diretor': dados['diretor'],
                'nota': nota,
                'categoria': categoria,
                'comentario': comentario,
                'poster_url': dados['poster_url'],
                'sinopse': dados['sinopse'],
                'elenco': dados['elenco'],
                'ano': dados['ano']
            })
        
        return {
            'filmes': filmes_para_adicionar,
            'erros': erros,
            'total': len(filmes_para_adicionar),
            'erros_count': len(erros)
        }
        
    except Exception as e:
        return {'erro': f'Erro ao processar arquivo: {str(e)}'}
    detail_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    detail_params = {"api_key": API_KEY, "language": "pt-BR", "append_to_response": "credits"}
    try:
        data = requests.get(detail_url, params=detail_params, verify=False, timeout=10).json()

        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        elenco = ", ".join([ator['name'] for ator in data.get('credits', {}).get('cast', [])[:3]])
        diretor = next((m['name'] for m in data.get('credits', {}).get('crew', []) if m['job'] == 'Director'), "Desconhecido")
        genero = ", ".join([g['name'] for g in data.get('genres', [])[:3]]) if data.get('genres') else "N/A"
        ator_principal = elenco.split(", ")[0] if elenco else "N/A"
        rotten_rt = "N/A"

        return {
            "titulo": data.get('title'),
            "diretor": diretor,
            "sinopse": data.get('overview'),
            "elenco": elenco,
            "poster_url": poster_url,
            "ano": data.get('release_date', '0000')[:4],
            "genero": genero,
            "ator_principal": ator_principal,
            "rotten_tomatoes": rotten_rt,
            "tmdb_id": tmdb_id
        }
    except Exception as e:
        print(f"ERRO NA BUSCA POR ID: {e}")
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    filmes_assistidos = conn.execute('SELECT * FROM filmes ORDER BY id DESC').fetchall()
    futuros = conn.execute('SELECT * FROM lista_futuros ORDER BY id DESC').fetchall()
    categorias_futuros = set()
    for futuro in futuros:
        if futuro['categoria']:
            for item in futuro['categoria'].split(','):
                cat = item.strip()
                if cat:
                    categorias_futuros.add(cat)
    categorias_assistidos = set()
    for filme in filmes_assistidos:
        if filme['categoria']:
            for item in filme['categoria'].split(','):
                cat = item.strip()
                if cat:
                    categorias_assistidos.add(cat)
    conn.close()
    return render_template('index.html', filmes=filmes_assistidos, futuros=futuros, categorias_futuros=sorted(categorias_futuros), categorias_assistidos=sorted(categorias_assistidos))

# Rotas existentes (adicionar, deletar)...
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if request.method == 'POST':
        titulo_busca = request.form['titulo']
        nota = request.form['nota']
        comentario = request.form['comentario']
        categoria = request.form.get('categoria', '').strip()
        dados = buscar_dados_tmdb(titulo_busca)
        if dados:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO filmes (titulo, diretor, nota, comentario, categoria, poster_url, sinopse, elenco, ano)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (dados['titulo'], dados['diretor'], nota, comentario, categoria,
                  dados['poster_url'], dados['sinopse'], dados['elenco'], dados['ano']))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('adicionar.html')

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM filmes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    filme = conn.execute('SELECT * FROM filmes WHERE id = ?', (id,)).fetchone()
    if not filme:
        conn.close()
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        diretor = request.form['diretor']
        nota = request.form['nota']
        comentario = request.form['comentario']
        categoria = request.form.get('categoria', '').strip()
        conn.execute('''
            UPDATE filmes SET titulo = ?, diretor = ?, nota = ?, comentario = ?, categoria = ? WHERE id = ?
        ''', (titulo, diretor, nota, comentario, categoria, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('editar.html', filme=filme)

@app.route('/editar_futuro/<int:id>', methods=['GET', 'POST'])
def editar_futuro(id):
    conn = get_db_connection()
    futuro = conn.execute('SELECT * FROM lista_futuros WHERE id = ?', (id,)).fetchone()
    if not futuro:
        conn.close()
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        diretor = request.form['diretor']
        genero = request.form['genero']
        ator_principal = request.form['ator_principal']
        prioridade = request.form.get('prioridade', futuro['prioridade'])
        categoria = request.form.get('categoria', futuro['categoria'] or '').strip()
        conn.execute('''
            UPDATE lista_futuros
            SET titulo = ?, diretor = ?, genero = ?, ator_principal = ?, prioridade = ?, categoria = ?
            WHERE id = ?
        ''', (titulo, diretor, genero, ator_principal, prioridade, categoria, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('editar_futuro.html', futuro=futuro)

# NOVAS ROTAS: Lista Futuros
@app.route('/adicionar_futuro', methods=['POST'])
def adicionar_futuro():
    titulo_busca = request.form['titulo']
    dados = buscar_dados_tmdb(titulo_busca)
    if dados:
        conn = get_db_connection()
        try:
            prioridade = int(request.form.get('prioridade', 3))
        except ValueError:
            prioridade = 3
        prioridade = max(1, min(5, prioridade))
        categoria = request.form.get('categoria', '').strip()
        try:
            conn.execute('''
                INSERT INTO lista_futuros (titulo, diretor, genero, ator_principal, prioridade, categoria, rotten_tomatoes, poster_url, sinopse, tmdb_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (dados['titulo'], dados['diretor'], dados['genero'], dados['ator_principal'], prioridade, categoria,
                  dados['rotten_tomatoes'], dados['poster_url'], dados['sinopse'], dados['tmdb_id']))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Duplicata ignorada
        conn.close()
        return redirect(url_for('index'))
    return "Filme não encontrado"

@app.route('/deletar_futuro/<int:id>', methods=['POST'])
def deletar_futuro(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM lista_futuros WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/importar_excel', methods=['GET', 'POST'])
def importar_excel():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Processar o arquivo
            resultado = processar_excel_filmes(filepath)
            
            # Limpar arquivo após processamento
            os.remove(filepath)
            
            if 'erro' in resultado:
                flash(resultado['erro'])
                return redirect(request.url)
            
            # Adicionar filmes ao banco
            conn = get_db_connection()
            adicionados = 0
            erros_adicao = []
            
            for filme in resultado['filmes']:
                try:
                    conn.execute('''
                        INSERT INTO filmes (titulo, diretor, nota, comentario, categoria, poster_url, sinopse, elenco, ano)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        filme['titulo'], filme['diretor'], filme['nota'], filme['comentario'],
                        filme['categoria'], filme['poster_url'], filme['sinopse'], 
                        filme['elenco'], filme['ano']
                    ))
                    adicionados += 1
                except Exception as e:
                    erros_adicao.append(f"Erro ao adicionar '{filme['titulo']}': {str(e)}")
            
            conn.commit()
            conn.close()
            
            # Mensagem de sucesso
            mensagem = f"{adicionados} filmes importados com sucesso!"
            if resultado['erros']:
                mensagem += f" {len(resultado['erros'])} filmes não puderam ser processados."
            if erros_adicao:
                mensagem += f" {len(erros_adicao)} filmes não puderam ser salvos."
            
            flash(mensagem)
            return redirect(url_for('index'))
        else:
            flash('Tipo de arquivo não permitido. Use apenas .xlsx ou .xls')
            return redirect(request.url)
    
    return render_template('importar_excel.html')
@app.route('/marcar_assistido/<int:id>', methods=['POST'])
def marcar_assistido(id):
    conn = get_db_connection()
    futuro = conn.execute('SELECT * FROM lista_futuros WHERE id = ?', (id,)).fetchone()
    if not futuro:
        conn.close()
        return redirect(url_for('index'))


    if not dados:
        dados = {
            'titulo': futuro['titulo'],
            'diretor': futuro['diretor'],
            'poster_url': futuro['poster_url'],
            'sinopse': futuro['sinopse'],
            'elenco': '',
            'ano': None
        }

    conn.execute('''
        INSERT INTO filmes (titulo, diretor, nota, comentario, categoria, poster_url, sinopse, elenco, ano)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados['titulo'],
        dados['diretor'],
        None,
        None,
        futuro['categoria'],  # Copiar categoria do futuro
        dados['poster_url'],
        dados['sinopse'],
        dados['elenco'],
        dados['ano']
    ))
    conn.execute('DELETE FROM lista_futuros WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# API JSON pra busca/filtros no popover (AJAX)
@app.route('/api/buscar_futuros')
def api_buscar_futuros():
    query = request.args.get('q', '')
    diretor = request.args.get('diretor', '')
    genero = request.args.get('genero', '')
    ator = request.args.get('ator', '')
    rt_min = request.args.get('rt_min', '0')
    
    # CORREÇÃO: Busca na TMDB, NÃO na lista_futuros (que está vazia)
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": API_KEY, 
        "query": query, 
        "language": "pt-BR",
        "page": 1
    }
    
    try:
        response = requests.get(search_url, params=params, verify=False, timeout=10)
        if response.status_code != 200:
            return jsonify([])
            
        search_res = response.json()
        resultados = []
        
        for filme in search_res.get('results', [])[:10]:  # Top 10 resultados
            filme_id = filme['id']
            detail_url = f"https://api.themoviedb.org/3/movie/{filme_id}"
            detail_params = {"api_key": API_KEY, "language": "pt-BR", "append_to_response": "credits"}
            
            data = requests.get(detail_url, params=detail_params, verify=False, timeout=5).json()
            
            # Aplica filtros
            filme_diretor = next((m['name'] for m in data.get('credits', {}).get('crew', []) if m['job'] == 'Director'), "")
            filme_genero = ", ".join([g['name'] for g in data.get('genres', [])[:3]])
            filme_ator = next((a['name'] for a in data.get('credits', {}).get('cast', [])), "")
            
            if diretor and diretor.lower() not in filme_diretor.lower():
                continue
            if genero and genero.lower() not in filme_genero.lower():
                continue
            if ator and ator.lower() not in filme_ator.lower():
                continue
            
            poster_path = data.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            
            resultados.append({
                'id': filme_id,
                'titulo': data.get('title', filme['title']),
                'diretor': filme_diretor,
                'genero': filme_genero,
                'ator_principal': filme_ator,
                'poster_url': poster_url,
                'sinopse': data.get('overview', '')
            })
            
        return jsonify(resultados)
        
    except Exception as e:
        print(f"Erro API: {e}")
        return jsonify([])

@app.route('/adicionar_futuro_page', methods=['GET'])
def adicionar_futuro_page():
    return render_template('adicionar_futuro.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)