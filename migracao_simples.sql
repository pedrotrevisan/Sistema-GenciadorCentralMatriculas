-- ============================================
-- MIGRAÇÃO SIMPLES: Adicionar 8 novos campos TOTVS
-- Sistema Central de Matrículas - SENAI CIMATEC
-- Data: 2026-01-22
-- 
-- ATENÇÃO: Execute apenas UMA VEZ!
-- Se der erro de "column already exists", as colunas já foram criadas.
-- ============================================

ALTER TABLE alunos ADD COLUMN rg_data_emissao VARCHAR(10);
ALTER TABLE alunos ADD COLUMN naturalidade VARCHAR(100);
ALTER TABLE alunos ADD COLUMN naturalidade_uf VARCHAR(2);
ALTER TABLE alunos ADD COLUMN sexo VARCHAR(1);
ALTER TABLE alunos ADD COLUMN cor_raca VARCHAR(20);
ALTER TABLE alunos ADD COLUMN grau_instrucao VARCHAR(50);
ALTER TABLE alunos ADD COLUMN nome_pai VARCHAR(200);
ALTER TABLE alunos ADD COLUMN nome_mae VARCHAR(200);

-- Verificar se deu certo
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'alunos';
