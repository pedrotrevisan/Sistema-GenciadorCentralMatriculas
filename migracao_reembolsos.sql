-- ============================================
-- MIGRAÇÃO: Módulo de Reembolsos
-- Sistema Central de Matrículas - SENAI CIMATEC
-- Data: 2026-01-22
-- ============================================

-- Tabela de Reembolsos
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reembolsos') THEN
        CREATE TABLE reembolsos (
            id VARCHAR(36) PRIMARY KEY,
            
            -- Dados do Aluno
            aluno_nome VARCHAR(200) NOT NULL,
            aluno_cpf VARCHAR(14),
            curso VARCHAR(200) NOT NULL,
            turma VARCHAR(100),
            
            -- Dados da Solicitação
            motivo VARCHAR(100) NOT NULL,
            motivo_descricao TEXT,
            reter_taxa BOOLEAN DEFAULT FALSE,
            
            -- Chamado SGC Plus
            numero_chamado_sgc VARCHAR(50),
            
            -- Datas do Fluxo
            data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_retorno_financeiro TIMESTAMP,
            data_provisao_pagamento TIMESTAMP,
            data_pagamento TIMESTAMP,
            
            -- Status
            status VARCHAR(50) NOT NULL DEFAULT 'aberto',
            observacoes TEXT,
            
            -- Auditoria
            criado_por_id VARCHAR(36) NOT NULL REFERENCES usuarios(id),
            criado_por_nome VARCHAR(200) NOT NULL,
            atualizado_por_id VARCHAR(36) REFERENCES usuarios(id),
            atualizado_por_nome VARCHAR(200),
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_reembolsos_status ON reembolsos(status);
        CREATE INDEX idx_reembolsos_created ON reembolsos(created_at);
        CREATE INDEX idx_reembolsos_aluno ON reembolsos(aluno_nome);
        
        RAISE NOTICE 'Tabela reembolsos criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela reembolsos já existe';
    END IF;
END $$;

-- ============================================
-- Motivos de Reembolso Disponíveis (referência)
-- ============================================
-- sem_escolaridade  - Sem Escolaridade (não reter taxa)
-- sem_vaga          - Sem Vaga 2026.1 (não reter taxa)
-- passou_bolsista   - Passou como Bolsista (não reter taxa)
-- nao_tem_vaga      - Não Tem Vaga (não reter taxa)
-- desistencia       - Desistência do Aluno (RETER 10%)
-- outros            - Outros (não reter taxa)

-- ============================================
-- Status do Fluxo de Reembolso
-- ============================================
-- aberto                      - Aberto
-- aguardando_dados_bancarios  - Aguardando Dados Bancários
-- enviado_financeiro          - Enviado ao Financeiro
-- pago                        - Pago
-- cancelado                   - Cancelado

-- ============================================
-- Verificação final
-- ============================================
SELECT 'reembolsos' as tabela, count(*) as registros FROM reembolsos;
