"""Exportador XLSX para TOTVS - Padrão Strategy"""
from abc import ABC, abstractmethod
from typing import List, BinaryIO
from io import BytesIO
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import csv

from src.domain.entities import PedidoMatricula


class IExportadorArquivo(ABC):
    """Interface para exportadores de arquivo - Strategy Pattern"""

    @abstractmethod
    def exportar(self, pedidos: List[PedidoMatricula]) -> BytesIO:
        """Exporta pedidos para o formato específico"""
        pass

    @abstractmethod
    def get_content_type(self) -> str:
        """Retorna o content-type do arquivo"""
        pass

    @abstractmethod
    def get_extension(self) -> str:
        """Retorna a extensão do arquivo"""
        pass


class ExportadorXLSXTOTVS(IExportadorArquivo):
    """Exportador para Excel no formato TOTVS"""

    def exportar(self, pedidos: List[PedidoMatricula]) -> BytesIO:
        """Exporta pedidos para XLSX no layout TOTVS"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Matrículas TOTVS"

        # Estilos
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="004587", end_color="004587", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Cabeçalhos conforme layout TOTVS
        headers = [
            "CODIGO_PEDIDO", "DATA_PEDIDO", "CONSULTOR", "CURSO", 
            "PROJETO", "EMPRESA", "CPF_ALUNO", "NOME_ALUNO", 
            "EMAIL_ALUNO", "TELEFONE_ALUNO", "DATA_NASCIMENTO",
            "RG", "ORGAO_EMISSOR", "UF_RG", "CEP", "LOGRADOURO",
            "NUMERO", "COMPLEMENTO", "BAIRRO", "CIDADE", "UF",
            "STATUS", "DATA_EXPORTACAO"
        ]

        # Aplica cabeçalhos
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # Dados
        row = 2
        data_exportacao = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        for pedido in pedidos:
            for aluno in pedido.alunos:
                ws.cell(row=row, column=1, value=pedido.id).border = thin_border
                ws.cell(row=row, column=2, value=pedido.created_at.strftime("%d/%m/%Y")).border = thin_border
                ws.cell(row=row, column=3, value=pedido.consultor_nome).border = thin_border
                ws.cell(row=row, column=4, value=pedido.curso_nome).border = thin_border
                ws.cell(row=row, column=5, value=pedido.projeto_nome or "").border = thin_border
                ws.cell(row=row, column=6, value=pedido.empresa_nome or "").border = thin_border
                ws.cell(row=row, column=7, value=aluno.cpf.formatado()).border = thin_border
                ws.cell(row=row, column=8, value=aluno.nome).border = thin_border
                ws.cell(row=row, column=9, value=aluno.email.valor).border = thin_border
                ws.cell(row=row, column=10, value=aluno.telefone.formatado()).border = thin_border
                ws.cell(row=row, column=11, value=aluno.data_nascimento.strftime("%d/%m/%Y")).border = thin_border
                ws.cell(row=row, column=12, value=aluno.rg).border = thin_border
                ws.cell(row=row, column=13, value=aluno.rg_orgao_emissor).border = thin_border
                ws.cell(row=row, column=14, value=aluno.rg_uf).border = thin_border
                ws.cell(row=row, column=15, value=aluno.endereco_cep).border = thin_border
                ws.cell(row=row, column=16, value=aluno.endereco_logradouro).border = thin_border
                ws.cell(row=row, column=17, value=aluno.endereco_numero).border = thin_border
                ws.cell(row=row, column=18, value=aluno.endereco_complemento or "").border = thin_border
                ws.cell(row=row, column=19, value=aluno.endereco_bairro).border = thin_border
                ws.cell(row=row, column=20, value=aluno.endereco_cidade).border = thin_border
                ws.cell(row=row, column=21, value=aluno.endereco_uf).border = thin_border
                ws.cell(row=row, column=22, value=pedido.status.label).border = thin_border
                ws.cell(row=row, column=23, value=data_exportacao).border = thin_border
                row += 1

        # Ajusta largura das colunas
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

        # Salva em BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    def get_content_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def get_extension(self) -> str:
        return "xlsx"


class ExportadorCSVTOTVS(IExportadorArquivo):
    """Exportador para CSV no formato TOTVS"""

    def exportar(self, pedidos: List[PedidoMatricula]) -> BytesIO:
        """Exporta pedidos para CSV no layout TOTVS"""
        output = BytesIO()
        
        headers = [
            "CODIGO_PEDIDO", "DATA_PEDIDO", "CONSULTOR", "CURSO",
            "PROJETO", "EMPRESA", "CPF_ALUNO", "NOME_ALUNO",
            "EMAIL_ALUNO", "TELEFONE_ALUNO", "DATA_NASCIMENTO",
            "RG", "ORGAO_EMISSOR", "UF_RG", "CEP", "LOGRADOURO",
            "NUMERO", "COMPLEMENTO", "BAIRRO", "CIDADE", "UF",
            "STATUS", "DATA_EXPORTACAO"
        ]
        
        # Escreve em modo texto
        import io
        text_output = io.StringIO()
        writer = csv.writer(text_output, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        
        data_exportacao = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        for pedido in pedidos:
            for aluno in pedido.alunos:
                writer.writerow([
                    pedido.id,
                    pedido.created_at.strftime("%d/%m/%Y"),
                    pedido.consultor_nome,
                    pedido.curso_nome,
                    pedido.projeto_nome or "",
                    pedido.empresa_nome or "",
                    aluno.cpf.formatado(),
                    aluno.nome,
                    aluno.email.valor,
                    aluno.telefone.formatado(),
                    aluno.data_nascimento.strftime("%d/%m/%Y"),
                    aluno.rg,
                    aluno.rg_orgao_emissor,
                    aluno.rg_uf,
                    aluno.endereco_cep,
                    aluno.endereco_logradouro,
                    aluno.endereco_numero,
                    aluno.endereco_complemento or "",
                    aluno.endereco_bairro,
                    aluno.endereco_cidade,
                    aluno.endereco_uf,
                    pedido.status.label,
                    data_exportacao
                ])
        
        # Converte para bytes
        output.write(text_output.getvalue().encode('utf-8-sig'))
        output.seek(0)
        return output

    def get_content_type(self) -> str:
        return "text/csv"

    def get_extension(self) -> str:
        return "csv"


class ExportadorFactory:
    """Factory para criar exportadores - Factory Pattern"""

    _exportadores = {
        "xlsx": ExportadorXLSXTOTVS,
        "csv": ExportadorCSVTOTVS
    }

    @classmethod
    def criar(cls, formato: str) -> IExportadorArquivo:
        """Cria exportador baseado no formato"""
        formato = formato.lower()
        if formato not in cls._exportadores:
            raise ValueError(f"Formato não suportado: {formato}")
        return cls._exportadores[formato]()

    @classmethod
    def formatos_disponiveis(cls) -> list:
        """Retorna lista de formatos disponíveis"""
        return list(cls._exportadores.keys())
