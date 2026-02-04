import requests
import random
from datetime import datetime, timedelta

API_URL = "https://matricula-central.preview.emergentagent.com/api"

# Login como admin
login_resp = requests.post(f"{API_URL}/auth/login", json={
    "email": "admin@senai.br",
    "senha": "admin123"
})
TOKEN = login_resp.json()["token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# CPFs válidos para teste (gerados)
CPFS_VALIDOS = [
    "52998224725", "71428793860", "89532476103", "45678912304", "12345678909",
    "98765432100", "11122233396", "44455566638", "77788899900", "33344455527",
    "66677788856", "99900011185", "22233344414", "55566677743", "88899900072"
]

# Nomes realistas brasileiros
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

# Cursos disponíveis
CURSOS = [
    {"id": "c1", "nome": "Técnico em Automação Industrial"},
    {"id": "c2", "nome": "Técnico em Mecatrônica"},
    {"id": "c3", "nome": "Técnico em Eletrotécnica"},
    {"id": "c4", "nome": "Engenharia de Software"},
    {"id": "c5", "nome": "Análise de Dados"},
]

# Projetos
PROJETOS = [
    {"id": "p1", "nome": "Projeto Jovem Aprendiz"},
    {"id": "p2", "nome": "Projeto SENAI de Inovação"},
    {"id": "p3", "nome": "Capacitação Industrial 4.0"},
]

# Empresas
EMPRESAS = [
    {"id": "e1", "nome": "Petrobras S.A."},
    {"id": "e2", "nome": "Ford Motor Company Brasil"},
    {"id": "e3", "nome": "Braskem S.A."},
]

# Bairros de Salvador
BAIRROS = ["Pituba", "Barra", "Ondina", "Itaigara", "Caminho das Árvores", "Paralela", "Stella Maris", "Piatã"]
LOGRADOUROS = ["Rua das Flores", "Avenida Tancredo Neves", "Rua do Sol", "Avenida Paulo VI", "Rua da Paz", "Alameda das Árvores"]

def criar_pedido(index, aluno_data, cpf, curso, vinculo, data_criacao):
    """Cria um pedido via API"""
    
    # Definir se é projeto ou empresa
    if vinculo["tipo"] == "projeto":
        projeto_id = vinculo["id"]
        projeto_nome = vinculo["nome"]
        empresa_id = None
        empresa_nome = None
    else:
        projeto_id = None
        projeto_nome = None
        empresa_id = vinculo["id"]
        empresa_nome = vinculo["nome"]
    
    payload = {
        "curso_id": curso["id"],
        "curso_nome": curso["nome"],
        "projeto_id": projeto_id,
        "projeto_nome": projeto_nome,
        "empresa_id": empresa_id,
        "empresa_nome": empresa_nome,
        "observacoes": f"Pedido de teste #{index + 1} - Criado para demonstração",
        "alunos": [{
            "nome": aluno_data["nome"],
            "cpf": cpf,
            "email": aluno_data["email"],
            "telefone": f"719{random.randint(10000000, 99999999)}",
            "data_nascimento": f"{random.randint(1985, 2005)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "rg": f"{random.randint(1000000, 9999999)}",
            "rg_orgao_emissor": "SSP",
            "rg_uf": "BA",
            "endereco_cep": f"41{random.randint(100, 999)}000",
            "endereco_logradouro": random.choice(LOGRADOUROS),
            "endereco_numero": str(random.randint(10, 999)),
            "endereco_complemento": random.choice(["Apto 101", "Casa", "Bloco B", "", "Sala 5"]),
            "endereco_bairro": random.choice(BAIRROS),
            "endereco_cidade": "Salvador",
            "endereco_uf": "BA"
        }]
    }
    
    response = requests.post(f"{API_URL}/pedidos", json=payload, headers=HEADERS)
    return response

def atualizar_status(pedido_id, novo_status):
    """Atualiza o status de um pedido"""
    payload = {"novo_status": novo_status}
    response = requests.patch(f"{API_URL}/pedidos/{pedido_id}/status", json=payload, headers=HEADERS)
    return response

print("🚀 Criando 15 pedidos de teste para o vídeo...")
print("=" * 60)

# Distribuir status: 5 Pendente, 4 Em Análise, 4 Aprovado, 2 Realizado
STATUS_DISTRIBUICAO = [
    "pendente", "pendente", "pendente", "pendente", "pendente",
    "em_analise", "em_analise", "em_analise", "em_analise",
    "aprovado", "aprovado", "aprovado", "aprovado",
    "realizado", "realizado"
]
random.shuffle(STATUS_DISTRIBUICAO)

# Datas distribuídas nos últimos 3 meses
hoje = datetime.now()
datas = []
for i in range(15):
    dias_atras = random.randint(0, 90)
    datas.append(hoje - timedelta(days=dias_atras))
datas.sort()  # Ordenar por data

pedidos_criados = []

for i in range(15):
    aluno = ALUNOS[i]
    cpf = CPFS_VALIDOS[i]
    curso = random.choice(CURSOS)
    
    # Alternar entre projeto e empresa
    if i % 2 == 0:
        vinculo = {"tipo": "projeto", **random.choice(PROJETOS)}
    else:
        vinculo = {"tipo": "empresa", **random.choice(EMPRESAS)}
    
    status_final = STATUS_DISTRIBUICAO[i]
    
    print(f"\n📝 Pedido {i+1}/15: {aluno['nome'][:30]}...")
    print(f"   Curso: {curso['nome']}")
    print(f"   Vínculo: {vinculo['nome']}")
    print(f"   Status final: {status_final}")
    
    # Criar pedido
    resp = criar_pedido(i, aluno, cpf, curso, vinculo, datas[i])
    
    if resp.status_code in [200, 201]:
        pedido = resp.json()
        pedido_id = pedido.get("id")
        protocolo = pedido.get("numero_protocolo", "N/A")
        print(f"   ✅ Criado! Protocolo: {protocolo}")
        
        # Atualizar status se não for pendente
        if status_final != "pendente" and pedido_id:
            # Precisa seguir o fluxo: pendente -> em_analise -> aprovado -> realizado
            if status_final in ["em_analise", "aprovado", "realizado"]:
                atualizar_status(pedido_id, "em_analise")
                print(f"   📊 Status: pendente → em_analise")
            
            if status_final in ["aprovado", "realizado"]:
                atualizar_status(pedido_id, "aprovado")
                print(f"   📊 Status: em_analise → aprovado")
            
            if status_final == "realizado":
                atualizar_status(pedido_id, "realizado")
                print(f"   📊 Status: aprovado → realizado")
        
        pedidos_criados.append({"protocolo": protocolo, "nome": aluno["nome"], "status": status_final})
    else:
        print(f"   ❌ Erro: {resp.status_code} - {resp.text[:100]}")

print("\n" + "=" * 60)
print(f"🎉 {len(pedidos_criados)} pedidos criados com sucesso!")
print("\n📋 Resumo:")
print("-" * 60)

for p in pedidos_criados:
    print(f"   {p['protocolo']} | {p['nome'][:35]:<35} | {p['status']}")

print("\n✅ Pronto para gravar o vídeo!")
print("   Dashboard vai mostrar:")
print("   - 15 pedidos no total")
print("   - 5 Pendentes, 4 Em Análise, 4 Aprovados, 2 Realizados")
print("   - Gráfico de evolução mensal com dados dos últimos 3 meses")
