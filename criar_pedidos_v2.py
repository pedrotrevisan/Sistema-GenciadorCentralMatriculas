import requests
import random

API_URL = "https://totvs-assist.preview.emergentagent.com/api"

# Login como admin
login_resp = requests.post(f"{API_URL}/auth/login", json={
    "email": "admin@senai.br",
    "senha": "admin123"
})
TOKEN = login_resp.json()["token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def gerar_cpf_valido():
    """Gera um CPF válido"""
    def calcula_digito(cpf_parcial):
        soma = 0
        peso = len(cpf_parcial) + 1
        for digito in cpf_parcial:
            soma += int(digito) * peso
            peso -= 1
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)
    
    cpf = [str(random.randint(0, 9)) for _ in range(9)]
    cpf.append(calcula_digito(cpf))
    cpf.append(calcula_digito(cpf))
    return ''.join(cpf)

# Dados realistas
ALUNOS = [
    {"nome": "Pedro Henrique Trevisan Passos Costa", "email": "pedro.costa@gmail.com"},
    {"nome": "Maria Eduarda Santos Silva", "email": "maria.silva@hotmail.com"},
    {"nome": "João Carlos de Oliveira Junior", "email": "joao.oliveira@gmail.com"},
    {"nome": "Ana Beatriz Ferreira Lima", "email": "ana.lima@outlook.com"},
    {"nome": "Lucas Gabriel Souza Pereira", "email": "lucas.pereira@gmail.com"},
    {"nome": "Julia Cristina Almeida Rocha", "email": "julia.rocha@gmail.com"},
    {"nome": "Matheus Felipe Santos Costa", "email": "matheus.costa@hotmail.com"},
    {"nome": "Isabela Carolina Martins Nunes", "email": "isabela.nunes@gmail.com"},
    {"nome": "Gabriel Augusto Lima Barbosa", "email": "gabriel.barbosa@outlook.com"},
    {"nome": "Larissa Vitória Cardoso Dias", "email": "larissa.dias@gmail.com"},
    {"nome": "Rafael Eduardo Gomes Ribeiro", "email": "rafael.ribeiro@hotmail.com"},
    {"nome": "Beatriz Helena Castro Mendes", "email": "beatriz.mendes@gmail.com"},
    {"nome": "Thiago Henrique Araujo Fernandes", "email": "thiago.fernandes@outlook.com"},
    {"nome": "Carolina Maria Pinto Correia", "email": "carolina.correia@gmail.com"},
    {"nome": "Vinícius Augusto Moreira Teixeira", "email": "vinicius.teixeira@hotmail.com"},
]

CURSOS = [
    {"id": "c1", "nome": "Técnico em Automação Industrial"},
    {"id": "c2", "nome": "Técnico em Mecatrônica"},
    {"id": "c3", "nome": "Técnico em Eletrotécnica"},
    {"id": "c4", "nome": "Engenharia de Software"},
    {"id": "c5", "nome": "Análise de Dados"},
]

PROJETOS = [
    {"id": "p1", "nome": "Projeto Jovem Aprendiz"},
    {"id": "p2", "nome": "Projeto SENAI de Inovação"},
    {"id": "p3", "nome": "Capacitação Industrial 4.0"},
]

EMPRESAS = [
    {"id": "e1", "nome": "Petrobras S.A."},
    {"id": "e2", "nome": "Ford Motor Company Brasil"},
    {"id": "e3", "nome": "Braskem S.A."},
]

BAIRROS = ["Pituba", "Barra", "Ondina", "Itaigara", "Caminho das Árvores", "Paralela", "Stella Maris"]
LOGRADOUROS = ["Rua das Flores", "Avenida Tancredo Neves", "Rua do Sol", "Avenida Paulo VI", "Rua da Paz"]

# Distribuição de status
STATUS_DIST = ["pendente"]*5 + ["em_analise"]*4 + ["aprovado"]*4 + ["realizado"]*2
random.shuffle(STATUS_DIST)

print("🚀 Criando 15 pedidos de teste com CPFs válidos...")
print("=" * 60)

pedidos_criados = []
cpfs_usados = set()

for i, aluno in enumerate(ALUNOS):
    # Gerar CPF único válido
    while True:
        cpf = gerar_cpf_valido()
        if cpf not in cpfs_usados:
            cpfs_usados.add(cpf)
            break
    
    curso = CURSOS[i % len(CURSOS)]
    status_final = STATUS_DIST[i]
    
    # Alternar projeto/empresa
    if i % 2 == 0:
        projeto = random.choice(PROJETOS)
        payload = {
            "curso_id": curso["id"],
            "curso_nome": curso["nome"],
            "projeto_id": projeto["id"],
            "projeto_nome": projeto["nome"],
            "empresa_id": None,
            "empresa_nome": None,
            "observacoes": f"Pedido de teste #{i+1}",
            "alunos": [{
                "nome": aluno["nome"],
                "cpf": cpf,
                "email": aluno["email"],
                "telefone": f"719{random.randint(10000000, 99999999)}",
                "data_nascimento": f"{random.randint(1990, 2002)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "rg": f"{random.randint(1000000, 9999999)}",
                "rg_orgao_emissor": "SSP",
                "rg_uf": "BA",
                "endereco_cep": f"41{random.randint(100, 999)}000",
                "endereco_logradouro": random.choice(LOGRADOUROS),
                "endereco_numero": str(random.randint(10, 999)),
                "endereco_complemento": random.choice(["Apto 101", "Casa", "", "Bloco B"]),
                "endereco_bairro": random.choice(BAIRROS),
                "endereco_cidade": "Salvador",
                "endereco_uf": "BA"
            }]
        }
        vinculo = projeto["nome"]
    else:
        empresa = random.choice(EMPRESAS)
        payload = {
            "curso_id": curso["id"],
            "curso_nome": curso["nome"],
            "projeto_id": None,
            "projeto_nome": None,
            "empresa_id": empresa["id"],
            "empresa_nome": empresa["nome"],
            "observacoes": f"Pedido de teste #{i+1}",
            "alunos": [{
                "nome": aluno["nome"],
                "cpf": cpf,
                "email": aluno["email"],
                "telefone": f"719{random.randint(10000000, 99999999)}",
                "data_nascimento": f"{random.randint(1990, 2002)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "rg": f"{random.randint(1000000, 9999999)}",
                "rg_orgao_emissor": "SSP",
                "rg_uf": "BA",
                "endereco_cep": f"41{random.randint(100, 999)}000",
                "endereco_logradouro": random.choice(LOGRADOUROS),
                "endereco_numero": str(random.randint(10, 999)),
                "endereco_complemento": random.choice(["Apto 101", "Casa", "", "Bloco B"]),
                "endereco_bairro": random.choice(BAIRROS),
                "endereco_cidade": "Salvador",
                "endereco_uf": "BA"
            }]
        }
        vinculo = empresa["nome"]
    
    print(f"\n📝 Pedido {i+1}/15: {aluno['nome'][:35]}")
    print(f"   CPF: {cpf} | Curso: {curso['nome'][:25]}")
    
    resp = requests.post(f"{API_URL}/pedidos", json=payload, headers=HEADERS)
    
    if resp.status_code in [200, 201]:
        pedido = resp.json()
        pedido_id = pedido.get("id")
        protocolo = pedido.get("numero_protocolo", "N/A")
        print(f"   ✅ Criado! Protocolo: {protocolo}")
        
        # Atualizar status
        if status_final != "pendente" and pedido_id:
            if status_final in ["em_analise", "aprovado", "realizado"]:
                requests.patch(f"{API_URL}/pedidos/{pedido_id}/status", 
                             json={"novo_status": "em_analise"}, headers=HEADERS)
            
            if status_final in ["aprovado", "realizado"]:
                requests.patch(f"{API_URL}/pedidos/{pedido_id}/status", 
                             json={"novo_status": "aprovado"}, headers=HEADERS)
            
            if status_final == "realizado":
                requests.patch(f"{API_URL}/pedidos/{pedido_id}/status", 
                             json={"novo_status": "realizado"}, headers=HEADERS)
            
            print(f"   📊 Status final: {status_final}")
        
        pedidos_criados.append({"protocolo": protocolo, "nome": aluno["nome"], "status": status_final})
    else:
        print(f"   ❌ Erro: {resp.status_code} - {resp.text[:80]}")

print("\n" + "=" * 60)
print(f"🎉 {len(pedidos_criados)} pedidos criados com sucesso!")
print("\n📋 Resumo Final:")
print("-" * 60)

for p in pedidos_criados:
    status_emoji = {"pendente": "🟡", "em_analise": "🔵", "aprovado": "🟢", "realizado": "✅"}
    emoji = status_emoji.get(p['status'], "⚪")
    print(f"   {p['protocolo']} | {p['nome'][:32]:<32} | {emoji} {p['status']}")

# Contagem
from collections import Counter
status_count = Counter([p['status'] for p in pedidos_criados])
print("\n📊 Distribuição de Status:")
print(f"   🟡 Pendente: {status_count.get('pendente', 0)}")
print(f"   🔵 Em Análise: {status_count.get('em_analise', 0)}")
print(f"   🟢 Aprovado: {status_count.get('aprovado', 0)}")
print(f"   ✅ Realizado: {status_count.get('realizado', 0)}")
