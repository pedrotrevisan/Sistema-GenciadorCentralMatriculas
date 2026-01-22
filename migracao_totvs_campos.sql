-- ============================================
-- MIGRAÇÃO: Adicionar 8 novos campos TOTVS
-- Sistema Central de Matrículas - SENAI CIMATEC
-- Data: 2026-01-22
-- ============================================

-- Verificar se as colunas já existem antes de adicionar
-- (evita erros se rodar o script mais de uma vez)

-- 1. Data de Emissão do RG
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'alunos' AND column_name = 'rg_data_emissao') THEN
        ALTER TABLE alunos ADD COLUMN rg_data_emissao VARCHAR(10);
        RAISE NOTICE 'Coluna rg_data_emissao adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna rg_data_emissao já existe';
    END IF;
END $$;

-- 2. Naturalidade (Cidade de nascimento)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'alunos' AND column_name = 'naturalidade') THEN
        ALTER TABLE alunos ADD COLUMN naturalidade VARCHAR(100);
        RAISE NOTICE 'Coluna naturalidade adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna naturalidade já existe';
    END IF;
END $$;

-- 3. Naturalidade UF (Estado de nascimento)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'alunos' AND column_name = 'naturalidade_uf') THEN
        ALTER TABLE alunos ADD COLUMN naturalidade_uf VARCHAR(2);
        RAISE NOTICE 'Coluna naturalidade_uf adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna naturalidade_uf já existe';
    END IF;
END $$;

-- 4. Sexo (M/F)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'alunos' AND column_name = 'sexo') THEN
        ALTER TABLE alunos ADD COLUMN sexo VARCHAR(1);
        RAISE NOTICE 'Coluna sexo adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna sexo já existe';
    END IF;
END $$;

-- 5. Cor/Raça
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'alunos' AND column_name = 'cor_raca') THEN
        ALTER TABLE alunos ADD COLUMN cor_raca VARCHAR(20);
        RAISE NOTICE 'Coluna cor_raca adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna cor_raca já existe';
    END IF;
END $$;

-- 6. Grau de Instrução
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'alunos' AND column_name = 'grau_instrucao') THEN
        ALTER TABLE alunos ADD COLUMN grau_instrucao VARCHAR(50);
        RAISE NOTICE 'Coluna grau_instrucao adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna grau_instrucao já existe';
    END IF;
END $$;

-- 7. Nome do Pai
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'alunos' AND column_name = 'nome_pai') THEN
        ALTER TABLE alunos ADD COLUMN nome_pai VARCHAR(200);
        RAISE NOTICE 'Coluna nome_pai adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna nome_pai já existe';
    END IF;
END $$;

-- 8. Nome da Mãe
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'alunos' AND column_name = 'nome_mae') THEN
        ALTER TABLE alunos ADD COLUMN nome_mae VARCHAR(200);
        RAISE NOTICE 'Coluna nome_mae adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna nome_mae já existe';
    END IF;
END $$;

-- ============================================
-- Verificação final - listar colunas da tabela alunos
-- ============================================
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'alunos'
ORDER BY ordinal_position;
