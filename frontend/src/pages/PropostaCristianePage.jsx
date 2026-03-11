import React from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  FileText,
  CheckCircle,
  AlertTriangle,
  Zap,
  BarChart3,
  Users,
  Clock,
  Target,
  ArrowRight,
  Building2,
  Heart,
  TrendingUp,
  Sparkles
} from 'lucide-react';

export default function PropostaCristianePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center items-center gap-3 mb-4">
            <img 
              src="https://customer-assets.emergentagent.com/job_matricula-hub/artifacts/p7o5gy77_logo_cimatec.jpg" 
              alt="SENAI CIMATEC"
              className="h-16 object-contain"
            />
          </div>
          <h1 className="text-3xl font-bold text-slate-800 mb-2">
            SYNAPSE
          </h1>
          <p className="text-lg text-blue-600 font-medium">
            Hub de Inteligência Operacional
          </p>
          <p className="text-slate-500 mt-2">
            Sistema Operacional da Central de Matrículas
          </p>
        </div>

        {/* Para quem */}
        <Card className="mb-6 border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <p className="text-sm text-blue-800">
              <strong>Para:</strong> Cristiane Mendes - Coordenadora CAC
            </p>
            <p className="text-sm text-blue-800">
              <strong>De:</strong> Pedro Passos
            </p>
            <p className="text-sm text-blue-800">
              <strong>Data:</strong> Março/2026
            </p>
          </CardContent>
        </Card>

        {/* Resumo Executivo */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-amber-500" />
              Resumo Executivo
            </h2>
            <p className="text-slate-600 leading-relaxed">
              O <strong>SYNAPSE</strong> é um sistema desenvolvido especificamente para resolver 
              os desafios operacionais da Central de Matrículas do SENAI CIMATEC. 
              O sistema está <strong>100% operacional em produção</strong> com dados reais (414 matrículas, 
              50 reembolsos, 10 turmas), substituindo completamente o controle em planilhas 
              Excel e a alimentação manual de relatórios.
            </p>
          </CardContent>
        </Card>

        {/* O Problema */}
        <Card className="mb-6 border-red-200">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold text-red-700 mb-4 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              O Desafio Atual
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                'Controle de vagas feito manualmente em planilhas',
                'Contagem linha por linha para saber ocupação',
                'Alimentação manual do PowerBI',
                'Pendências documentais em abas separadas',
                'Sem histórico centralizado de contatos com alunos',
                'Retrabalho constante para consolidar informações'
              ].map((item, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-red-500 mt-1">✗</span>
                  <span className="text-slate-600 text-sm">{item}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* A Solução */}
        <Card className="mb-6 border-green-200">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold text-green-700 mb-4 flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              A Solução: SYNAPSE
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                'Painel visual de ocupação de vagas por curso',
                'Dashboards em tempo real (BI, SLA, Gestão)',
                'Central de Pendências Documentais integrada',
                'Kanban visual com drag & drop',
                'Histórico completo de interações',
                'Importação em lote via Excel',
                'Gestão de Reembolsos',
                'Assistente TOTVS para preenchimento'
              ].map((item, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span className="text-slate-600 text-sm">{item}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Números */}
        <Card className="mb-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Sistema Já Operacional
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-4xl font-bold">414</p>
                <p className="text-sm opacity-80">Matrículas</p>
              </div>
              <div>
                <p className="text-4xl font-bold">50</p>
                <p className="text-sm opacity-80">Reembolsos</p>
              </div>
              <div>
                <p className="text-4xl font-bold">10</p>
                <p className="text-sm opacity-80">Turmas</p>
              </div>
              <div>
                <p className="text-4xl font-bold">89.5%</p>
                <p className="text-sm opacity-80">Ocupação</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-white/20 text-center">
              <p className="text-sm opacity-80">420 vagas totais • 376 ocupadas • 44 disponíveis</p>
            </div>
          </CardContent>
        </Card>

        {/* Situação das Turmas */}
        <Card className="mb-6 border-amber-200 bg-amber-50">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold text-amber-700 mb-4 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Situação Atual das Turmas (Dados Reais)
            </h2>
            <div className="space-y-2">
              {[
                { curso: 'Técnico em Mecânica', ocupadas: 46, vagas: 42, status: 'lotado' },
                { curso: 'Técnico em Redes de Computadores', ocupadas: 46, vagas: 42, status: 'lotado' },
                { curso: 'Técnico em Manutenção Automotiva', ocupadas: 42, vagas: 42, status: 'lotado' },
                { curso: 'Técnico em Petroquímica', ocupadas: 40, vagas: 42, status: 'lotando' },
                { curso: 'Técnico em Mecatrônica', ocupadas: 39, vagas: 42, status: 'lotando' },
                { curso: 'Técnico em Eletrotécnica', ocupadas: 38, vagas: 42, status: 'lotando' },
              ].map((turma, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-white rounded-lg">
                  <span className="text-slate-700 text-sm">{turma.curso}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{turma.ocupadas}/{turma.vagas}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      turma.status === 'lotado' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {turma.status === 'lotado' ? 'LOTADO' : 'LOTANDO'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-amber-600 mt-3 text-center">
              * 3 cursos lotados, 3 cursos acima de 90% de ocupação
            </p>
          </CardContent>
        </Card>

        {/* Módulos */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Target className="h-5 w-5 text-blue-600" />
              Módulos Disponíveis
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                { nome: 'Painel de Controle', desc: 'KPIs clicáveis em tempo real', icon: BarChart3 },
                { nome: 'Painel de Vagas', desc: 'Ocupação visual por curso/turma', icon: Users },
                { nome: 'Kanban', desc: 'Fluxo visual de matrículas', icon: Target },
                { nome: 'Central de Pendências', desc: 'Gestão de documentos pendentes', icon: FileText },
                { nome: 'Reembolsos', desc: 'Controle de solicitações de reembolso', icon: TrendingUp },
                { nome: 'Dashboard BI', desc: 'Gráficos, funis e análises', icon: BarChart3 },
                { nome: 'Dashboard SLA', desc: 'Métricas e prazos de atendimento', icon: Clock },
                { nome: 'Chamados SGC', desc: 'Demandas BMP do SGC Plus', icon: FileText },
                { nome: 'Dashboard Produtividade', desc: 'Desempenho individual da equipe', icon: TrendingUp },
                { nome: 'Central de Alertas', desc: 'Notificações e retornos pendentes', icon: Zap },
                { nome: 'Importação em Lote', desc: 'Upload em massa via Excel/CSV', icon: Sparkles },
                { nome: 'Assistente TOTVS', desc: 'Auxílio no preenchimento do ERP', icon: Zap },
                { nome: 'Apoio Cognitivo', desc: 'Base de conhecimento e tarefas diárias', icon: Heart },
                { nome: 'Modo Apresentação', desc: 'Slides para reuniões com dados ao vivo', icon: Sparkles },
              ].map((modulo, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                  <modulo.icon className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="font-medium text-slate-800">{modulo.nome}</p>
                    <p className="text-xs text-slate-500">{modulo.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Benefícios */}
        <Card className="mb-6 border-amber-200 bg-amber-50">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold text-amber-700 mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Benefícios Esperados
            </h2>
            <div className="space-y-3">
              {[
                { titulo: 'Redução de tempo', desc: 'De 30 minutos para 5 segundos para ver ocupação de vagas' },
                { titulo: 'Eliminação de retrabalho', desc: 'Sem necessidade de manter múltiplas planilhas atualizadas' },
                { titulo: 'Visibilidade em tempo real', desc: 'Dashboards sempre atualizados, sem alimentação manual' },
                { titulo: 'Rastreabilidade', desc: 'Histórico completo de todas as interações e mudanças de status' },
                { titulo: 'Padronização', desc: 'Todos usando a mesma fonte de informação' },
              ].map((beneficio, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-800">{beneficio.titulo}</p>
                    <p className="text-sm text-slate-600">{beneficio.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Próximos Passos */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
              <ArrowRight className="h-5 w-5 text-blue-600" />
              Próximos Passos Sugeridos
            </h2>
            <div className="space-y-3">
              {[
                { passo: '✓', titulo: 'Desenvolvimento', desc: 'Sistema desenvolvido e em produção', done: true },
                { passo: '2', titulo: 'Validação com a Equipe', desc: 'Apresentação e treinamento da equipe CAC', done: false },
                { passo: '3', titulo: 'Integração TOTVS', desc: 'Proposta ao NDSI para automatizar importação de dados', done: false },
                { passo: '4', titulo: 'Expansão', desc: 'Novos módulos e melhorias baseadas no feedback da equipe', done: false },
              ].map((item, idx) => (
                <div key={idx} className={`flex items-center gap-4 p-3 rounded-lg ${item.done ? 'bg-green-50' : 'bg-slate-50'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${item.done ? 'bg-green-500 text-white' : 'bg-[#004587] text-white'}`}>
                    {item.passo}
                  </div>
                  <div>
                    <p className="font-medium text-slate-800">{item.titulo}</p>
                    <p className="text-sm text-slate-500">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Acesso */}
        <Card className="mb-6 bg-gradient-to-r from-slate-800 to-slate-900 text-white">
          <CardContent className="p-6 text-center">
            <h2 className="text-xl font-bold mb-4">Acesse o Sistema</h2>
            <div className="space-y-2">
              <p className="text-blue-300">🔗 synapse.pedrotrevisan.dev.br</p>
              <p className="text-sm opacity-70">Login: cristiane.mendes@fieb.org.br</p>
            </div>
            <div className="mt-4 pt-4 border-t border-white/20">
              <p className="text-sm opacity-70">
                Modo Apresentação: /apresentacao
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-slate-500 text-sm">
          <p>Desenvolvido com dedicação para a equipe CAC</p>
          <p className="flex items-center justify-center gap-1 mt-1">
            <Heart className="h-4 w-4 text-red-400" />
            SENAI CIMATEC 2026
          </p>
        </div>

      </div>
    </div>
  );
}
