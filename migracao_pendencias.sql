-- ============================================
-- MIGRAÇÃO: Central de Pendências Documentais
-- Sistema Central de Matrículas - SENAI CIMATEC
-- Data: 2026-01-22
-- ============================================

-- 1. Tabela de Tipos de Documento
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tipos_documento') THEN
        CREATE TABLE tipos_documento (
            id VARCHAR(36) PRIMARY KEY,
            codigo VARCHAR(10) UNIQUE NOT NULL,
            nome VARCHAR(200) NOT NULL,
            obrigatorio BOOLEAN DEFAULT TRUE,
            observacoes TEXT,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_tipos_documento_codigo ON tipos_documento(codigo);
        
        RAISE NOTICE 'Tabela tipos_documento criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela tipos_documento já existe';
    END IF;
END $$;

-- 2. Tabela de Pendências
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pendencias') THEN
        CREATE TABLE pendencias (
            id VARCHAR(36) PRIMARY KEY,
            aluno_id VARCHAR(36) NOT NULL REFERENCES alunos(id),
            pedido_id VARCHAR(36) NOT NULL REFERENCES pedidos(id),
            tipo_documento_id VARCHAR(36) REFERENCES tipos_documento(id),
            documento_codigo VARCHAR(10) NOT NULL,
            documento_nome VARCHAR(200) NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'pendente',
            observacoes TEXT,
            motivo_rejeicao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        );
        
        CREATE INDEX idx_pendencias_aluno ON pendencias(aluno_id);
        CREATE INDEX idx_pendencias_pedido ON pendencias(pedido_id);
        CREATE INDEX idx_pendencias_status ON pendencias(status);
        CREATE INDEX idx_pendencias_created ON pendencias(created_at);
        
        RAISE NOTICE 'Tabela pendencias criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela pendencias já existe';
    END IF;
END $$;

-- 3. Tabela de Histórico de Contatos
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'historico_contatos') THEN
        CREATE TABLE historico_contatos (
            id VARCHAR(36) PRIMARY KEY,
            pendencia_id VARCHAR(36) NOT NULL REFERENCES pendencias(id) ON DELETE CASCADE,
            usuario_id VARCHAR(36) NOT NULL REFERENCES usuarios(id),
            usuario_nome VARCHAR(200) NOT NULL,
            tipo_contato VARCHAR(30) NOT NULL,
            descricao TEXT NOT NULL,
            resultado VARCHAR(50),
            data_contato TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_historico_contatos_pendencia ON historico_contatos(pendencia_id);
        
        RAISE NOTICE 'Tabela historico_contatos criada com sucesso';
    ELSE
        RAISE NOTICE 'Tabela historico_contatos já existe';
    END IF;
END $$;

-- 4. Inserir Tipos de Documento Padrão
INSERT INTO tipos_documento (id, codigo, nome, obrigatorio, observacoes) VALUES
    (gen_random_uuid()::text, '94', 'Comprovante de Residência', true, 'PDF ou JPG – Máx. 10MB'),
    (gen_random_uuid()::text, '96', 'Solicitação Desconto (Sindicato/CIEB/Ex-Aluno/Col. Sistema FIEB)', false, 'Se aplicável'),
    (gen_random_uuid()::text, '97', 'CPF/RG Responsável Legal (menor de 18 anos)', false, 'Se aplicável'),
    (gen_random_uuid()::text, '131', 'RG – Frente', true, 'PDF ou JPG – Máx. 10MB'),
    (gen_random_uuid()::text, '132', 'RG – Verso', true, 'PDF ou JPG – Máx. 10MB'),
    (gen_random_uuid()::text, '136', 'Comprovante de Escolaridade – Frente', true, 'Histórico ou Atestado - PDF ou JPG – Máx. 10MB'),
    (gen_random_uuid()::text, '137', 'Comprovante de Escolaridade – Verso', true, 'Histórico ou Atestado - PDF ou JPG – Máx. 10MB'),
    (gen_random_uuid()::text, '205', 'CPF', false, 'PDF ou JPG – Máx. 10MB')
ON CONFLICT (codigo) DO NOTHING;

-- ============================================
-- Verificação final
-- ============================================
SELECT 'tipos_documento' as tabela, count(*) as registros FROM tipos_documento
UNION ALL
SELECT 'pendencias' as tabela, count(*) as registros FROM pendencias
UNION ALL
SELECT 'historico_contatos' as tabela, count(*) as registros FROM historico_contatos;
