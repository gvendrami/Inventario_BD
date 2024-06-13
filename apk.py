import os
from flask import Flask, make_response, request
from pymongo import MongoClient
import json

apk_bd = Flask(__name__)

URI = os.getenv('URI', 'mongodb://localhost:27017/')

client = MongoClient(URI)

c_funcionarios = MongoClient(URI)['inventario']['funcionarios']

## criei as funções que vou utilizar mais de uma vez em um route para facilitar, o resto eu nem criei função pois utilizei uma vez memso

def verif_ativos(): ## salva os ativos, ja que vou utilizar duas vezes (att e remover os ativos)
    ativos_existentes = {"notebook": ['modelo', 'tag', 'versao', 'caracteristicas'],
                         "desktop": ['modelo', 'tag', 'versao', 'caracteristicas'],
                         "monitor1": ['modelo'],
                         "monitor2": ['modelo'],
                         "teclado": ['modelo'],
                         "mouse": ['modelo'],
                         "nobreak": ['modelo'],
                         "headset": ['modelo'],
                         "celular": ['modelo', 'numero'],
                         "acessorios": None
                        }

    return ativos_existentes

@apk_bd.route('/', methods=['POST'])
def novo_funcionario():
    dados = request.get_json()

    if not dados:
        response = make_response(json.dumps({'message': 'Sem dados.'}), 400)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    sem_cpf_nome = [insert for insert in ['cpf', 'nome'] if not dados.get(insert)]  
    if sem_cpf_nome:    ## aqui valida se tem ou nao o cpf e nome. caso nao tenha, ele barra aqui mesmo                               
        response = make_response(json.dumps({'message': f'{sem_cpf_nome[0]} é necessário.'}), 400)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    if c_funcionarios.find_one({'cpf': dados['cpf']}):  ## aqui valida se o cpf inserido ja esta cadastrado no sistema para nao haver duplicidade de dados sensiveis
        response = make_response(json.dumps({'message': 'CPF já cadastrado no sistema.'}), 400)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    inserir_funcionario = {
    "cpf": dados['cpf'],           ## CPF e nome sem get pois sao obrigatorios nesse caso, por isso nao utiliza o  get. é necessario entao a confirmação deles quando usar essa função no caso obviamewnte
    "nome": dados['nome'],
    "notebook": {"modelo": dados.get('notebook_modelo'),
                 "tag": dados.get('notebook_tag'),
                 "versao": dados.get('notebook_versao'),
                 "caracteristicas": dados.get('notebook_caracteristicas')},
    "monitor1": {"modelo": dados.get('monitor1_modelo')},
    "monitor2": {"modelo": dados.get('monitor2_modelo')},
    "teclado": {"modelo": dados.get('teclado_modelo')},
    "mouse": {"modelo": dados.get('mouse_modelo')},
    "nobreak": {"modelo": dados.get('nobreak_modelo')},
    "desktop": {"modelo": dados.get('desktop_modelo'),
                "tag": dados.get('desktop_tag'),
                "versao": dados.get('desktop_versao'),
                "caracteristicas": dados.get('desktop_caracteristicas')},
    "headset": {"modelo": dados.get('headset_modelo')},
    "celular": {"modelo": dados.get('celular_modelo'),
                "numero": dados.get('celular_numero')},
    "acessorios": dados.get('acessorios')
    }

    c_funcionarios.insert_one(inserir_funcionario)  ## aqui ele insere um novo funcionario apos as verificacoes
    response = make_response(json.dumps({'message': 'Concluido!'}), 201)
    response.headers['Content-Type'] = 'application/json'

    return response

@apk_bd.route('/', methods=['GET'])
def lista_dos_funcionarios():
    funcionarios = [funcionario for funcionario in c_funcionarios.find({}, {'_id': 0})] ## puxa todos os funcionarios sem trazer o id

    response = make_response(json.dumps(funcionarios), 200)
    response.headers['Content-Type'] = 'application/json'

    return response

@apk_bd.route('/<cpf>', methods=['GET'])
def funcionario_especifico(cpf):
    funcionario = c_funcionarios.find_one({'cpf': cpf}, {'_id': 0})  ## aqui puxa um funcionario que tem o cpf especificado sem trrazer o id novamente

    if funcionario:
        response = make_response(json.dumps(funcionario), 200)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    else:
        response = make_response(json.dumps({'message': 'O funcionário especificado não foi encontrado'}), 404)
        response.headers['Content-Type'] = 'application/json'

        return response

@apk_bd.route('/<cpf>', methods=['PUT'])
def att_funcionario(cpf):
    data = request.get_json()

    if not data:
        response = make_response(json.dumps({'message': 'Sem dados.'}), 400)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    atualizado = c_funcionarios.update_one({'cpf': cpf}, {'$set': {campo: valor for campo, valor in data.items() if campo == 'nome'}}) ## aqui atualiza os dados apos passar pela proxima verificacao, claro

    if atualizado > 0:
        response = make_response(json.dumps({'message': 'Colaborador atualizado com sucesso!'}), 200)

    else:
        response = make_response(json.dumps({'message': 'Funcionário não foi encontrado no sistema.'}), 404)

    response.headers['Content-Type'] = 'application/json'

    return response

@apk_bd.route('/<cpf>/<ativos>', methods=['PUT'])
def att_ativos(cpf, ativos):
    dados = request.get_json()

    if not dados:
        response = make_response(json.dumps({'message': 'Sem dados.'}), 400)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    ativos_existentes = verif_ativos()

    if ativos not in ativos_existentes:
        response = make_response(json.dumps({'message': 'Ativo não existe.'}), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    ## esse att_campos é especifico para atualizar os dados, nao tem mt segredo pra falar a vdd. ele pega os dados ja existentes e substitui. essa parte é apenas os ativos no caso. passa por duas verificacoes antes de ser atualizado de fato
    att_campos = {f"{ativos}.{campos}": valor for campos, valor in dados.items() if campos in ativos_existentes[ativos]} if ativos_existentes[ativos] else {ativos: dados.get(ativos)}
    
    if not att_campos:
        response = make_response(json.dumps({'message': 'Sem campo para atualização encontrado.'}), 400)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    updated = c_funcionarios.update_one({'cpf': cpf}, {'$set': att_campos})

    if updated > 0:
        response = make_response(json.dumps({'message': f'{ativos} foi atualizado.'}), 200)
    else:
        response = make_response(json.dumps({'message': 'Funcionário não encontrado.'}), 404)
    
    response.headers['Content-Type'] = 'application/json'

    return response

@apk_bd.route('/<cpf>/<ativos>', methods=['DELETE'])
def remover_ativos(cpf, ativos):
    ativos_existentes = verif_ativos()

    if ativos not in ativos_existentes:
        response = make_response(json.dumps({'message': 'Ativo não existe.'}), 400)
        response.headers['Content-Type'] = 'application/json'

        return response
    
    ## esse att_campos é especifico para remover os dados. ele pega os dados especificados ja existentes e os remove. essa parte é apenas os ativos no caso. passa por duas verificacoes antes de ser removido de fato
    att_campos = {f"{ativos}.{campo}": None for campo in ativos_existentes[ativos]} if ativos_existentes[ativos] else {ativos: None}

    if not att_campos:
        response = make_response(json.dumps({'message': 'Sem campo para atualização encontrado.'}), 400)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    updated = c_funcionarios.update_one({'cpf': cpf}, {'$set': att_campos})

    if updated > 0:
        response = make_response(json.dumps({'message': f'{ativos} foi atualizado.'}), 200)
    else:
        response = make_response(json.dumps({'message': 'Funcionário não encontrado.'}), 404)
    
    response.headers['Content-Type'] = 'application/json'

    return response

@apk_bd.route('/<cpf>', methods=['DELETE'])
def remover_funcionario(cpf):
    funcionario = c_funcionarios.find_one({'cpf': cpf})

    if funcionario:

        ativos_existentes = verif_ativos()

        for ativo in ativos_existentes:

            if isinstance(funcionario.get(ativo), dict) and any(funcionario[ativo].values()) or funcionario.get(ativo): ## verifica se o ativo é um dicionario e se tem algum ativo com valor ou se nao tem um dicionario. em ambos os casos, terá a mesma mensagem.
                response = make_response(json.dumps({'message': 'O funcionário possui ativos.'}), 400)
                response.headers['Content-Type'] = 'application/json'

                return response
        
        c_funcionarios.delete_one({'cpf': cpf})
        response = make_response(json.dumps({'message': 'O funcionário foi removido do sistema.'}), 200)
        response.headers['Content-Type'] = 'application/json'

        return response

    response = make_response(json.dumps({'message': 'Funcionário não encontrado no sistema.'}), 404)
    response.headers['Content-Type'] = 'application/json'

    return response

if __name__ == '__main__':
    apk_bd.run(debug=True)