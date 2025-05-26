#Flask é um framework para Python que facilita a criação de aplicações web(sites e APIs), o código abaixo importa a class Flask e várias outras funções auxuliares desse mesmo.
from flask import Flask, render_template, request, redirect, url_for, session

#Importa o conector á base de dados MySQL
import mysql.connector

#Importa o módulo threading para criar threads(tarefas que rodam ao mesmo tempo)
import threading 

#Importa o módulo para abrir o navegador web padrão do sistema
import webbrowser

#Importa um módulo para interagir com o sistema operativo(não utilizado no código)
import os

#Cria a aplicação Flask. "app" vai ser o objeto principal do site.
app = Flask(__name__)

#Esta chave é utilizada para proteger os dados da sessão(dados guardados pelo utilizador)
app.secret_key = 'jorge_cheira_mal' #NUNCA DEIXAR ESTA CHAVE EXPOSTA EM SISTEMAS REAIS

#Função que cria e retorna a conexão com a base de dados MySQL
def get_bdconnection():
    #Mysql.connector.connect() é uma função que cria uma conexão com a base de dados MySQL
    #Recebe como parâmetros o endereço, user, a passe e base de dados
    return mysql.connector.connect(
        host = 'localhost', #localhost indica que a base de dados está na própria máquina
        user = 'root', #Substitui pelo teu user MySQL
        password = 'root', #Substitui pela tua password MySQL
        database = 'databasedef' #nome da base de dados que foi criada
    )

#Definimos uma rota(endereço) da aplicação com @app.route
#Aqui é a rota principal "/" que corresponde à página inicial do site - o login.
@app.route('/', methods=['GET', 'POST']) #Aqui permitimos os métodos GET(quando visita a página) e POST(quando envia o formulário)
def login():
    if request.method == 'POST': #Se o método for post vv
            username = request.form['username'] #Pega o username do formulário
            password = request.form['passuser'] #Pega a password do formulário
            conn = get_bdconnection() #Faz a conexão com a base de dados
            cursor = conn.cursor(dictionary=True) #Cria um cursor para executar comandos SQL ler resultados
            #^^(Dictionary=True), faz com que os resultados sejam dicionários, para aceder facilmente por nome das colunas
            cursor.execute("SELECT * FROM users WHERE username = %s AND passuser = %s", (username, password)) #Executa um comando SQL para selecionar o utilizador com o username e password
            #^^ o %s são marcadores de posição para evitar ataques de SQL injection
            user = cursor.fetchone() #Pega o primeiro resultado da consulta, ou none se não houver resultados
            cursor.close() #Fecha o cursor para libertar recursos
            conn.close() #Fecha a conexão com a base de dados

            if user: #Se encontrou um utilizador com o nome e password correta
                session['user_id'] = user['IDuser'] #Guarda o id do utilizador na sessão para lembrar quem está logado
                session['is_admin'] = user['is_admin'] == 1 #Cria uma variável na sessão para sabe se o utilizador é admin na sessão
                return redirect(url_for('admin' if session['is_admin'] else 'documentos')) #Redireciona para a página de admin se for admin, ou para a página documentos se for utilizador normal
            else: #Se não encontrou o utilizador
                return "Login Inválido!" #Retorna uma mensagem de erro
            
    return render_template('login.html') #Se o método for GET(não submeteu o formulário), renderiza a página de login

#Definimos a rota /documentos que mostra a lista dos documentos para utilizadores normais
@app.route('/documentos')
def documentos():
    if 'user_id' not in session: #Verifica se primeiro se alguém está logado, verificando se 'user_id' está na sessão
        return redirect(url_for('login')) #Se não estiver, redireciona para a página de login
    conn = get_bdconnection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT files.*, users.username
        FROM files
        JOIN users ON files.IDuser = users.IDuser
    """) #Busca todos os resultados da consulta em uma lista
    documentos = cursor.fetchall() #Pega todos os resultados da consulta
    cursor.close()
    conn.close()

    return render_template('documentos.html', documentos=documentos) #Renderiza a página de documentos, passando a lista "documentos" para que o template possa mostrar a página

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session or not session['is_admin']: #Verifica se o utilizador está logado e se é admin
        return redirect(url_for('login')) #Se não for, redireciona para a página de login
    
    conn = get_bdconnection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        if 'add_user' in request.form:
            iduser = request.form['IDuser']
            username = request.form['username']
            password = request.form['passuser']
            is_admin = request.form['is_admin']
            cursor.execute("INSERT INTO users (IDuser, username, passuser, is_admin) VALUES (%s, %s, %s, %s)", (iduser, username, password, is_admin))
            conn.commit() #Confirma as alterações na base de dados
        elif 'add_document' in request.form:
            idfile = request.form['IDfile']
            filename = request.form['filename']
            filelink = request.form['filelink'] 
            Saveuser = session['user_id'] #Pega o ID do utilizador logado
            cursor.execute("INSERT INTO files (IDfile, filename, filelink, IDuser) VALUES (%s, %s, %s, %s)", (idfile, filename, filelink, Saveuser))
            conn.commit()

    cursor.execute("SELECT * FROM users") #Busca todos os resultados da consulta em uma lista
    users = cursor.fetchall() #Pega todos os resultados da consulta
    cursor.execute("""
        SELECT files.*, users.username
        FROM files
        JOIN users ON files.IDuser = users.IDuser
    """) #Busca todos os resultados da consulta em uma lista
    documentos = cursor.fetchall() #Pega todos os resultados da consulta
    cursor.close()
    conn.close()

    return render_template('admin.html', users=users, documentos=documentos) #Renderiza a página de admin, passando as listas "users" e "documentos" para que o template possa mostrar a página

@app.route('/logout')
def logout():
    session.clear() #Limpa a sessão, removendo todos os dados guardados(desloga o utilizador)
    return redirect(url_for('login'))

browser_opened = False #Variável para saber se o navegador foi aberto para evitar abrir várias vezes

def open_browser():
    global browser_opened #Usa a variável global

    if not browser_opened: #Se o navegador não foi aberto ainda
        webbrowser.open_new('http://127.0.0.1:5000/') #Abre o URL da aplicação no navegador padrão
        browser_opened = True #Marca como aberto para não abrir novamente

if __name__ == '__main__':
    threading.Timer(1.5, open_browser).start() #Cria uma thread(tarefa que roda ao mesmo tempo) que espera 1.5 segunos e chama open_browser
    app.run(debug=True, use_reloader = False) #Inicia o servidot Flask no modo de desenvolvimento(debug=True) para mostrar erros e permitir recarregar automaticamente as alterações
    #O parâmetro use_reloader=False evita que o servidor renicie automaticamente duas vezes, o que evita abrir duas janelas do navegador


