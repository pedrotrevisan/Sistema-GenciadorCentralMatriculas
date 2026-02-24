"""Serviço de Regras de Negócio SENAI - Prazos, Pré-Requisitos e Validações"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==================== TIPOS DE CURSO ====================

class TipoCurso(Enum):
    """Tipos de curso com suas regras específicas"""
    CAI_BAS = "cai_bas"  # Aprendizagem Industrial Básica
    CAI_TEC = "cai_tec"  # Aprendizagem Industrial Técnica
    CHP = "chp"  # Curso de Habilitação Profissional
    CHP_EBEP = "chp_ebep"  # CHP com EBEP
    CQPG = "cqpg"  # Qualificação Profissional
    CAPG = "capg"  # Aperfeiçoamento Profissional
    CURTA_DURACAO = "curta_duracao"
    POS_TECNICO = "pos_tecnico"
    TECNICO = "tecnico"
    GRADUACAO = "graduacao"
    POS_GRADUACAO = "pos_graduacao"
    LIVRE = "livre"


# ==================== REGRAS DE PRÉ-REQUISITOS ====================

REGRAS_PRE_REQUISITOS = {
    TipoCurso.CAI_BAS: {
        "idade_minima": 14,
        "idade_maxima": 21,  # Não se aplica a PCD
        "escolaridade_minima": "fundamental_incompleto",
        "documentos_obrigatorios": [
            "rg_frente", "rg_verso", "cpf", "comprovante_residencia",
            "atestado_matricula_escolar", "encaminhamento_empresa",
            "rg_responsavel", "cpf_responsavel", "termo_compromisso"
        ],
        "requer_empresa": True,
        "permite_gratuidade": True,
        "descricao": "Aprendizagem Industrial Básica - 14 a 21 anos"
    },
    TipoCurso.CAI_TEC: {
        "idade_minima": 14,
        "idade_maxima": 21,
        "escolaridade_minima": "medio_cursando",
        "documentos_obrigatorios": [
            "rg_frente", "rg_verso", "cpf", "comprovante_residencia",
            "historico_escolar", "encaminhamento_empresa", "termo_compromisso"
        ],
        "requer_empresa": True,
        "permite_gratuidade": True,
        "descricao": "Aprendizagem Industrial Técnica - 14 a 21 anos"
    },
    TipoCurso.CHP: {
        "idade_minima": 16,
        "idade_maxima": None,
        "escolaridade_minima": "medio_completo",
        "documentos_obrigatorios": [
            "rg_frente", "rg_verso", "cpf", "comprovante_residencia",
            "historico_escolar"
        ],
        "requer_empresa": False,
        "permite_gratuidade": True,
        "descricao": "Curso de Habilitação Profissional"
    },
    TipoCurso.TECNICO: {
        "idade_minima": 16,
        "idade_maxima": None,
        "escolaridade_minima": "medio_cursando",
        "documentos_obrigatorios": [
            "rg_frente", "rg_verso", "cpf", "comprovante_residencia",
            "historico_escolar"
        ],
        "requer_empresa": False,
        "permite_gratuidade": True,
        "descricao": "Curso Técnico"
    },
    TipoCurso.CURTA_DURACAO: {
        "idade_minima": 16,
        "idade_maxima": None,
        "escolaridade_minima": None,
        "documentos_obrigatorios": [
            "rg_frente", "cpf"
        ],
        "requer_empresa": False,
        "permite_gratuidade": False,
        "descricao": "Curso de Curta Duração"
    },
    TipoCurso.LIVRE: {
        "idade_minima": None,
        "idade_maxima": None,
        "escolaridade_minima": None,
        "documentos_obrigatorios": ["rg_frente", "cpf"],
        "requer_empresa": False,
        "permite_gratuidade": False,
        "descricao": "Curso Livre"
    }
}


# ==================== PRAZOS ====================

PRAZOS_SENAI = {
    "pendencia_documental_dias": 5,  # Prazo para regularizar documentos
    "nao_atende_requisito_dias": 0,  # Cancelamento imediato
    "pagamento_dias": 7,  # Prazo para pagamento após aprovação
    "matricula_web_horas": 4,  # Horas antes da aula para matrícula web
    "comunicacao_cancelamento_turma_horas": 48,  # Horas para avisar cancelamento
    "reembolso_dias_uteis": 15,  # Dias úteis para reembolso
}


# ==================== SERVIÇO DE VALIDAÇÃO ====================

class ValidadorPreRequisitos:
    """Validador de pré-requisitos para matrícula"""
    
    @staticmethod
    def calcular_idade(data_nascimento: datetime) -> int:
        """Calcula idade a partir da data de nascimento"""
        hoje = datetime.now(timezone.utc)
        if data_nascimento.tzinfo is None:
            data_nascimento = data_nascimento.replace(tzinfo=timezone.utc)
        idade = hoje.year - data_nascimento.year
        if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
            idade -= 1
        return idade
    
    @staticmethod
    def validar_idade(
        data_nascimento: datetime,
        tipo_curso: TipoCurso,
        is_pcd: bool = False
    ) -> Dict[str, Any]:
        """
        Valida se a idade está dentro dos requisitos do curso
        
        Args:
            data_nascimento: Data de nascimento do aluno
            tipo_curso: Tipo do curso
            is_pcd: Se o aluno é PCD (idade máxima não se aplica)
        
        Returns:
            Dict com status, mensagem e detalhes
        """
        regras = REGRAS_PRE_REQUISITOS.get(tipo_curso, {})
        idade = ValidadorPreRequisitos.calcular_idade(data_nascimento)
        
        idade_minima = regras.get("idade_minima")
        idade_maxima = regras.get("idade_maxima")
        
        # Idade máxima não se aplica a PCD para CAI
        if is_pcd and tipo_curso in [TipoCurso.CAI_BAS, TipoCurso.CAI_TEC]:
            idade_maxima = None
        
        erros = []
        
        if idade_minima and idade < idade_minima:
            erros.append(f"Idade mínima: {idade_minima} anos. Aluno tem {idade} anos.")
        
        if idade_maxima and idade > idade_maxima:
            erros.append(f"Idade máxima: {idade_maxima} anos. Aluno tem {idade} anos.")
        
        return {
            "valido": len(erros) == 0,
            "idade": idade,
            "idade_minima": idade_minima,
            "idade_maxima": idade_maxima,
            "is_pcd": is_pcd,
            "erros": erros
        }
    
    @staticmethod
    def validar_escolaridade(
        escolaridade_aluno: str,
        tipo_curso: TipoCurso
    ) -> Dict[str, Any]:
        """Valida se a escolaridade atende aos requisitos"""
        regras = REGRAS_PRE_REQUISITOS.get(tipo_curso, {})
        escolaridade_minima = regras.get("escolaridade_minima")
        
        if not escolaridade_minima:
            return {"valido": True, "mensagem": "Sem requisito de escolaridade"}
        
        # Hierarquia de escolaridade
        HIERARQUIA = [
            "fundamental_incompleto",
            "fundamental_completo",
            "medio_cursando",
            "medio_completo",
            "superior_cursando",
            "superior_completo",
            "pos_graduacao"
        ]
        
        try:
            nivel_aluno = HIERARQUIA.index(escolaridade_aluno.lower())
            nivel_minimo = HIERARQUIA.index(escolaridade_minima.lower())
            
            if nivel_aluno >= nivel_minimo:
                return {
                    "valido": True,
                    "escolaridade_aluno": escolaridade_aluno,
                    "escolaridade_minima": escolaridade_minima
                }
            else:
                return {
                    "valido": False,
                    "escolaridade_aluno": escolaridade_aluno,
                    "escolaridade_minima": escolaridade_minima,
                    "erro": f"Escolaridade mínima: {escolaridade_minima}. Aluno possui: {escolaridade_aluno}"
                }
        except ValueError:
            return {
                "valido": False,
                "erro": f"Escolaridade não reconhecida: {escolaridade_aluno}"
            }
    
    @staticmethod
    def validar_documentos(
        documentos_apresentados: List[str],
        tipo_curso: TipoCurso,
        is_menor: bool = False
    ) -> Dict[str, Any]:
        """Valida se todos os documentos obrigatórios foram apresentados"""
        regras = REGRAS_PRE_REQUISITOS.get(tipo_curso, {})
        docs_obrigatorios = set(regras.get("documentos_obrigatorios", []))
        docs_apresentados = set(documentos_apresentados)
        
        # Adicionar documentos de responsável se menor
        if is_menor:
            docs_obrigatorios.add("rg_responsavel")
            docs_obrigatorios.add("cpf_responsavel")
        
        faltantes = docs_obrigatorios - docs_apresentados
        extras = docs_apresentados - docs_obrigatorios
        
        return {
            "valido": len(faltantes) == 0,
            "documentos_obrigatorios": list(docs_obrigatorios),
            "documentos_apresentados": list(docs_apresentados),
            "documentos_faltantes": list(faltantes),
            "documentos_extras": list(extras),
            "percentual_completo": len(docs_apresentados & docs_obrigatorios) / len(docs_obrigatorios) * 100 if docs_obrigatorios else 100
        }
    
    @staticmethod
    def validar_completo(
        data_nascimento: datetime,
        escolaridade: str,
        documentos: List[str],
        tipo_curso: TipoCurso,
        is_pcd: bool = False,
        is_menor: bool = False,
        tem_empresa: bool = False
    ) -> Dict[str, Any]:
        """Validação completa de pré-requisitos"""
        regras = REGRAS_PRE_REQUISITOS.get(tipo_curso, {})
        
        # Validar idade
        validacao_idade = ValidadorPreRequisitos.validar_idade(
            data_nascimento, tipo_curso, is_pcd
        )
        
        # Validar escolaridade
        validacao_escolaridade = ValidadorPreRequisitos.validar_escolaridade(
            escolaridade, tipo_curso
        )
        
        # Validar documentos
        validacao_docs = ValidadorPreRequisitos.validar_documentos(
            documentos, tipo_curso, is_menor
        )
        
        # Validar vínculo com empresa (se necessário)
        validacao_empresa = {"valido": True}
        if regras.get("requer_empresa") and not tem_empresa:
            validacao_empresa = {
                "valido": False,
                "erro": "Este curso requer vínculo com empresa"
            }
        
        # Consolidar resultado
        todos_validos = all([
            validacao_idade["valido"],
            validacao_escolaridade["valido"],
            validacao_docs["valido"],
            validacao_empresa["valido"]
        ])
        
        erros = []
        if not validacao_idade["valido"]:
            erros.extend(validacao_idade.get("erros", []))
        if not validacao_escolaridade["valido"]:
            erros.append(validacao_escolaridade.get("erro", ""))
        if not validacao_docs["valido"]:
            erros.append(f"Documentos faltantes: {', '.join(validacao_docs['documentos_faltantes'])}")
        if not validacao_empresa["valido"]:
            erros.append(validacao_empresa.get("erro", ""))
        
        return {
            "aprovado": todos_validos,
            "tipo_curso": tipo_curso.value,
            "tipo_curso_descricao": regras.get("descricao", ""),
            "validacao_idade": validacao_idade,
            "validacao_escolaridade": validacao_escolaridade,
            "validacao_documentos": validacao_docs,
            "validacao_empresa": validacao_empresa,
            "erros": erros,
            "pode_prosseguir": todos_validos,
            "status_sugerido": "aprovado" if todos_validos else "nao_atende_requisito"
        }


# ==================== SERVIÇO DE PRAZOS ====================

class CalculadorPrazos:
    """Calculador de prazos e alertas"""
    
    @staticmethod
    def calcular_prazo_pendencia(data_criacao: datetime) -> Dict[str, Any]:
        """
        Calcula prazo de pendência documental (5 dias)
        
        Returns:
            Dict com data limite, dias restantes e nível de alerta
        """
        if data_criacao.tzinfo is None:
            data_criacao = data_criacao.replace(tzinfo=timezone.utc)
        
        prazo_dias = PRAZOS_SENAI["pendencia_documental_dias"]
        data_limite = data_criacao + timedelta(days=prazo_dias)
        agora = datetime.now(timezone.utc)
        
        dias_restantes = (data_limite - agora).days
        horas_restantes = (data_limite - agora).total_seconds() / 3600
        
        # Determinar nível de alerta
        if dias_restantes < 0:
            nivel_alerta = "expirado"
            cor = "red"
            mensagem = f"Prazo expirado há {abs(dias_restantes)} dias"
        elif dias_restantes == 0:
            nivel_alerta = "critico"
            cor = "red"
            mensagem = f"Expira hoje! ({int(horas_restantes)} horas restantes)"
        elif dias_restantes <= 2:
            nivel_alerta = "urgente"
            cor = "orange"
            mensagem = f"Expira em {dias_restantes} dias"
        else:
            nivel_alerta = "normal"
            cor = "yellow"
            mensagem = f"{dias_restantes} dias restantes"
        
        return {
            "data_criacao": data_criacao.isoformat(),
            "data_limite": data_limite.isoformat(),
            "prazo_dias": prazo_dias,
            "dias_restantes": dias_restantes,
            "horas_restantes": round(horas_restantes, 1),
            "nivel_alerta": nivel_alerta,
            "cor": cor,
            "mensagem": mensagem,
            "expirado": dias_restantes < 0
        }
    
    @staticmethod
    def calcular_prazo_pagamento(data_aprovacao: datetime) -> Dict[str, Any]:
        """Calcula prazo para pagamento após aprovação"""
        if data_aprovacao.tzinfo is None:
            data_aprovacao = data_aprovacao.replace(tzinfo=timezone.utc)
        
        prazo_dias = PRAZOS_SENAI["pagamento_dias"]
        data_limite = data_aprovacao + timedelta(days=prazo_dias)
        agora = datetime.now(timezone.utc)
        
        dias_restantes = (data_limite - agora).days
        
        return {
            "data_aprovacao": data_aprovacao.isoformat(),
            "data_limite": data_limite.isoformat(),
            "prazo_dias": prazo_dias,
            "dias_restantes": dias_restantes,
            "expirado": dias_restantes < 0
        }
    
    @staticmethod
    def calcular_sla(data_criacao: datetime, status_atual: str) -> Dict[str, Any]:
        """
        Calcula métricas de SLA para um pedido
        
        SLAs padrão CAC:
        - Análise documental: 2 dias úteis
        - Efetivação após aprovação: 1 dia útil
        - Resposta a pendências: 5 dias
        """
        if data_criacao.tzinfo is None:
            data_criacao = data_criacao.replace(tzinfo=timezone.utc)
        
        agora = datetime.now(timezone.utc)
        tempo_total = agora - data_criacao
        dias_corridos = tempo_total.days
        horas_corridas = tempo_total.total_seconds() / 3600
        
        # SLA por status
        sla_config = {
            "pendente": {"sla_dias": 1, "descricao": "Iniciar análise"},
            "inscricao": {"sla_dias": 1, "descricao": "Iniciar análise"},
            "em_analise": {"sla_dias": 2, "descricao": "Concluir análise"},
            "analise_documental": {"sla_dias": 2, "descricao": "Concluir análise"},
            "documentacao_pendente": {"sla_dias": 5, "descricao": "Aguardar documentos"},
            "aprovado": {"sla_dias": 1, "descricao": "Aguardar pagamento"},
            "aguardando_pagamento": {"sla_dias": 7, "descricao": "Confirmar pagamento"},
        }
        
        config = sla_config.get(status_atual, {"sla_dias": 0, "descricao": ""})
        sla_dias = config["sla_dias"]
        
        dentro_sla = dias_corridos <= sla_dias if sla_dias > 0 else True
        
        return {
            "status_atual": status_atual,
            "dias_corridos": dias_corridos,
            "horas_corridas": round(horas_corridas, 1),
            "sla_dias": sla_dias,
            "sla_descricao": config["descricao"],
            "dentro_sla": dentro_sla,
            "dias_atraso": max(0, dias_corridos - sla_dias) if sla_dias > 0 else 0
        }


# ==================== FUNÇÕES AUXILIARES ====================

def get_documentos_por_tipo_curso(tipo_curso: str) -> List[Dict[str, Any]]:
    """Retorna lista de documentos obrigatórios para um tipo de curso"""
    try:
        tipo = TipoCurso(tipo_curso)
        regras = REGRAS_PRE_REQUISITOS.get(tipo, {})
        docs = regras.get("documentos_obrigatorios", [])
        
        # Mapeamento de código para nome legível
        NOMES_DOCS = {
            "rg_frente": "RG - Frente",
            "rg_verso": "RG - Verso",
            "cpf": "CPF",
            "comprovante_residencia": "Comprovante de Residência",
            "historico_escolar": "Histórico Escolar",
            "atestado_matricula_escolar": "Atestado de Matrícula Escolar",
            "encaminhamento_empresa": "Encaminhamento da Empresa",
            "termo_compromisso": "Termo de Compromisso",
            "rg_responsavel": "RG do Responsável",
            "cpf_responsavel": "CPF do Responsável",
        }
        
        return [
            {
                "codigo": doc,
                "nome": NOMES_DOCS.get(doc, doc.replace("_", " ").title()),
                "obrigatorio": True
            }
            for doc in docs
        ]
    except ValueError:
        return []


def get_tipos_curso_disponiveis() -> List[Dict[str, Any]]:
    """Retorna lista de tipos de curso com suas regras"""
    return [
        {
            "tipo": tipo.value,
            "descricao": regras.get("descricao", ""),
            "idade_minima": regras.get("idade_minima"),
            "idade_maxima": regras.get("idade_maxima"),
            "escolaridade_minima": regras.get("escolaridade_minima"),
            "requer_empresa": regras.get("requer_empresa", False),
            "permite_gratuidade": regras.get("permite_gratuidade", False),
            "qtd_documentos": len(regras.get("documentos_obrigatorios", []))
        }
        for tipo, regras in REGRAS_PRE_REQUISITOS.items()
    ]
