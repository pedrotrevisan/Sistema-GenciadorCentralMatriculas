import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Book, Search, ChevronRight, ChevronDown,
  LayoutDashboard, Users, FileText, DollarSign,
  Clock, Kanban, BarChart3, Settings, HelpCircle,
  GraduationCap, Bell, Shield, Database, Zap,
  CheckCircle, AlertTriangle, Info, Lightbulb,
  Mail, Phone, MessageSquare
} from 'lucide-react';

// Dados do manual
const MODULOS = [
  {
    id: 'dashboard',
    titulo: 'Dashboard Principal',
    icone: LayoutDashboard,
    cor: 'blue',
    descricao: 'Visão geral do sistema com KPIs e métricas principais',
    funcionalidades: [
      'Visualização do total de solicitações de matrícula',
      'Cards com contagem por status (Pendente, Em Análise, Aprovado, etc.)',
      'Gráficos de evolução mensal',
      'Acesso rápido às últimas solicitações'
    ],
    dicas: [
      'Clique nos cards para filtrar a lista por status',
      'Os gráficos são atualizados em tempo real'
    ],
    perfis: ['admin', 'assistente', 'consultor']
  },
  {
    id: 'pedidos',
    titulo: 'Gestão de Pedidos',
    icone: FileText,
    cor: 'green',
    descricao: 'Gerenciamento completo das solicitações de matrícula',
    funcionalidades: [
      'Criar nova solicitação de matrícula',
      'Visualizar detalhes do pedido',
      'Alterar status do pedido',
      'Exportar para TOTVS',
      'Visualizar timeline de alterações',
      'Filtrar por status, consultor e período'
    ],
    dicas: [
      'Use o protocolo (CM-XXXX-XXXX) para busca rápida',
      'A timeline mostra todo o histórico de alterações',
      'Exportação gera arquivo compatível com TOTVS'
    ],
    perfis: ['admin', 'assistente', 'consultor']
  },
  {
    id: 'reembolsos',
    titulo: 'Módulo de Reembolsos',
    icone: DollarSign,
    cor: 'yellow',
    descricao: 'Controle de solicitações de reembolso de matrícula',
    funcionalidades: [
      'Registrar nova solicitação de reembolso',
      'Acompanhar status (Aberto, Aguardando, No Financeiro, Pago)',
      'Cadastrar dados bancários do aluno',
      'Gerar templates de email para comunicação',
      'Atribuir responsável pelo atendimento',
      'Excluir registros incorretos (apenas admin)'
    ],
    dicas: [
      'Cards são clicáveis para filtrar por status',
      'Para menor de idade, marque "Conta de Responsável"',
      'Use os templates de email para agilizar comunicação'
    ],
    perfis: ['admin', 'assistente']
  },
  {
    id: 'pendencias',
    titulo: 'Central de Pendências',
    icone: Clock,
    cor: 'orange',
    descricao: 'Gestão de documentos pendentes dos alunos',
    funcionalidades: [
      'Visualizar documentos faltantes por aluno',
      'Registrar envio de documentação',
      'Aprovar ou reprovar documentos',
      'Acompanhar prazo de entrega',
      'Enviar cobrança via WhatsApp'
    ],
    dicas: [
      'Documentos críticos aparecem em destaque',
      'O botão de WhatsApp copia a mensagem formatada'
    ],
    perfis: ['admin', 'assistente']
  },
  {
    id: 'kanban',
    titulo: 'Kanban de Matrículas',
    icone: Kanban,
    cor: 'purple',
    descricao: 'Visualização do fluxo de matrículas em formato Kanban',
    funcionalidades: [
      'Arrastar e soltar cards entre colunas',
      'Visualizar pedidos por status',
      'Alterar status rapidamente',
      'Filtrar por consultor ou período'
    ],
    dicas: [
      'Arraste os cards para alterar o status',
      'Cores indicam a prioridade do pedido'
    ],
    perfis: ['admin', 'assistente']
  },
  {
    id: 'usuarios',
    titulo: 'Gestão de Usuários',
    icone: Users,
    cor: 'indigo',
    descricao: 'Administração de usuários e permissões do sistema',
    funcionalidades: [
      'Criar novo usuário',
      'Editar perfil e permissões',
      'Ativar/Desativar usuário',
      'Resetar senha individual',
      'Resetar todas as senhas (emergência)',
      'Excluir usuário'
    ],
    dicas: [
      'Senha padrão após reset: Senai@2026',
      'Usuário deve trocar senha no primeiro acesso',
      'Perfis: Admin, Assistente, Consultor'
    ],
    perfis: ['admin']
  },
  {
    id: 'vagas',
    titulo: 'Painel de Vagas',
    icone: GraduationCap,
    cor: 'cyan',
    descricao: 'Controle visual de ocupação de vagas por turma',
    funcionalidades: [
      'Visualizar ocupação por curso',
      'Barras de progresso por turma',
      'Alertas de turmas lotando (>85%)',
      'Filtrar por turno (Matutino/Noturno)',
      'Cadastrar novas turmas'
    ],
    dicas: [
      'Turmas em vermelho estão quase lotadas',
      'Ocupação é calculada em tempo real'
    ],
    perfis: ['admin', 'assistente']
  },
  {
    id: 'meudia',
    titulo: 'Meu Dia',
    icone: Bell,
    cor: 'pink',
    descricao: 'Planejamento diário e lembretes pessoais',
    funcionalidades: [
      'Criar tarefas para o dia',
      'Definir horário para lembretes',
      'Marcar tarefas como concluídas',
      'Receber alertas no horário definido',
      'Visualizar retornos pendentes'
    ],
    dicas: [
      'Tarefas com horário aparecem como lembretes',
      'Alerta visual aparece quando chegar o horário',
      'Tarefas recorrentes repetem todos os dias'
    ],
    perfis: ['admin', 'assistente', 'consultor']
  },
  {
    id: 'cadastros',
    titulo: 'Gestão de Cadastros',
    icone: Database,
    cor: 'slate',
    descricao: 'Cadastro de cursos, projetos e empresas',
    funcionalidades: [
      'Cadastrar cursos (Técnico, Graduação, Pós, etc.)',
      'Cadastrar projetos',
      'Cadastrar empresas parceiras',
      'Filtrar por tipo de curso',
      'Editar e excluir cadastros'
    ],
    dicas: [
      'Cursos estão categorizados por tipo',
      'Cards são clicáveis para filtrar'
    ],
    perfis: ['admin']
  },
  {
    id: 'sla',
    titulo: 'Dashboard SLA',
    icone: BarChart3,
    cor: 'emerald',
    descricao: 'Métricas de SLA e produtividade da equipe',
    funcionalidades: [
      'Visualizar tempo médio de atendimento',
      'Acompanhar pedidos críticos (>48h parados)',
      'Ver ranking de produtividade',
      'Alertas de SLA em risco',
      'Evolução semanal de atendimentos'
    ],
    dicas: [
      'Pedidos críticos são destacados em vermelho',
      'SLA padrão: 48 horas para análise inicial'
    ],
    perfis: ['admin', 'assistente']
  }
];

const PERFIS_INFO = {
  admin: { label: 'Administrador', cor: 'bg-red-100 text-red-800', desc: 'Acesso total ao sistema' },
  assistente: { label: 'Assistente', cor: 'bg-blue-100 text-blue-800', desc: 'Gestão de pedidos e atendimento' },
  consultor: { label: 'Consultor', cor: 'bg-green-100 text-green-800', desc: 'Criação e acompanhamento de pedidos' }
};

const FAQ = [
  {
    pergunta: 'Como resetar minha senha?',
    resposta: 'Entre em contato com o administrador do sistema. Ele pode resetar sua senha através do menu Usuários > botão de chave ao lado do seu nome. A senha será resetada para "Senai@2026" e você deverá alterá-la no próximo login.'
  },
  {
    pergunta: 'Como exportar dados para o TOTVS?',
    resposta: 'Acesse o menu Pedidos > clique no botão "Exportar TOTVS". O sistema irá gerar um arquivo Excel com todos os pedidos com status "Realizado" prontos para importação no TOTVS.'
  },
  {
    pergunta: 'Por que meu lembrete não aparece?',
    resposta: 'Verifique se a tarefa foi criada com a data correta (data de hoje). Tarefas com datas futuras só aparecem no dia correspondente. Além disso, a tarefa precisa ter um horário definido para aparecer como lembrete.'
  },
  {
    pergunta: 'Como atribuir um pedido a outro usuário?',
    resposta: 'Na lista de pedidos ou reembolsos, clique no ícone de pessoa ao lado do item. Será aberto um modal para selecionar o novo responsável.'
  },
  {
    pergunta: 'Qual a diferença entre os perfis de usuário?',
    resposta: 'Admin: acesso total, pode gerenciar usuários e configurações. Assistente: pode gerenciar pedidos, reembolsos e pendências de todos. Consultor: só visualiza e gerencia seus próprios pedidos.'
  },
  {
    pergunta: 'Como funciona o alerta de vagas?',
    resposta: 'Turmas com ocupação acima de 85% são marcadas como "Lotando" e aparecem em destaque no Painel de Vagas. Quando atinge 100%, não é mais possível criar matrículas para aquela turma.'
  }
];

export default function ManualAjudaPage() {
  const [busca, setBusca] = useState('');
  const [moduloExpandido, setModuloExpandido] = useState(null);
  const [tabAtiva, setTabAtiva] = useState('modulos');

  const modulosFiltrados = MODULOS.filter(m => 
    m.titulo.toLowerCase().includes(busca.toLowerCase()) ||
    m.descricao.toLowerCase().includes(busca.toLowerCase()) ||
    m.funcionalidades.some(f => f.toLowerCase().includes(busca.toLowerCase()))
  );

  const faqFiltrado = FAQ.filter(f =>
    f.pergunta.toLowerCase().includes(busca.toLowerCase()) ||
    f.resposta.toLowerCase().includes(busca.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Book className="w-7 h-7 text-[#004587]" />
            Manual do Sistema
          </h1>
          <p className="text-slate-500">Documentação e ajuda para usar o SYNAPSE</p>
        </div>
      </div>

      {/* Busca */}
      <Card className="bg-gradient-to-r from-[#004587] to-[#0066cc] text-white">
        <CardContent className="p-6">
          <h2 className="text-xl font-semibold mb-2">Como podemos ajudar?</h2>
          <p className="text-white/80 mb-4">Busque por funcionalidades, módulos ou dúvidas frequentes</p>
          <div className="relative max-w-xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <Input
              placeholder="Buscar no manual..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              className="pl-10 bg-white text-slate-800"
            />
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={tabAtiva} onValueChange={setTabAtiva}>
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="modulos">Módulos</TabsTrigger>
          <TabsTrigger value="perfis">Perfis</TabsTrigger>
          <TabsTrigger value="faq">FAQ</TabsTrigger>
        </TabsList>

        {/* Tab Módulos */}
        <TabsContent value="modulos" className="mt-6">
          <div className="grid gap-4">
            {modulosFiltrados.map((modulo) => {
              const Icone = modulo.icone;
              const expandido = moduloExpandido === modulo.id;

              return (
                <Card 
                  key={modulo.id}
                  className={`cursor-pointer transition-all ${expandido ? 'ring-2 ring-[#004587]' : 'hover:shadow-md'}`}
                  onClick={() => setModuloExpandido(expandido ? null : modulo.id)}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg bg-${modulo.cor}-100`}>
                          <Icone className={`w-6 h-6 text-${modulo.cor}-600`} />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{modulo.titulo}</CardTitle>
                          <p className="text-sm text-slate-500">{modulo.descricao}</p>
                        </div>
                      </div>
                      {expandido ? (
                        <ChevronDown className="w-5 h-5 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-slate-400" />
                      )}
                    </div>
                  </CardHeader>

                  {expandido && (
                    <CardContent className="pt-0" onClick={(e) => e.stopPropagation()}>
                      <div className="border-t pt-4 mt-2 space-y-4">
                        {/* Perfis com acesso */}
                        <div>
                          <h4 className="text-sm font-medium text-slate-600 mb-2">Perfis com acesso:</h4>
                          <div className="flex gap-2">
                            {modulo.perfis.map(p => (
                              <Badge key={p} className={PERFIS_INFO[p].cor}>
                                {PERFIS_INFO[p].label}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        {/* Funcionalidades */}
                        <div>
                          <h4 className="text-sm font-medium text-slate-600 mb-2 flex items-center gap-1">
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            Funcionalidades:
                          </h4>
                          <ul className="space-y-1">
                            {modulo.funcionalidades.map((f, i) => (
                              <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                                <span className="text-green-500 mt-1">•</span>
                                {f}
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* Dicas */}
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                          <h4 className="text-sm font-medium text-amber-800 mb-2 flex items-center gap-1">
                            <Lightbulb className="w-4 h-4" />
                            Dicas:
                          </h4>
                          <ul className="space-y-1">
                            {modulo.dicas.map((d, i) => (
                              <li key={i} className="text-sm text-amber-700">
                                💡 {d}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  )}
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Tab Perfis */}
        <TabsContent value="perfis" className="mt-6">
          <div className="grid md:grid-cols-3 gap-6">
            {Object.entries(PERFIS_INFO).map(([key, perfil]) => (
              <Card key={key} className="overflow-hidden">
                <div className={`h-2 ${perfil.cor.replace('text', 'bg').split(' ')[0]}`} />
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    {perfil.label}
                  </CardTitle>
                  <p className="text-sm text-slate-500">{perfil.desc}</p>
                </CardHeader>
                <CardContent>
                  <h4 className="text-sm font-medium mb-2">Módulos com acesso:</h4>
                  <div className="flex flex-wrap gap-2">
                    {MODULOS.filter(m => m.perfis.includes(key)).map(m => {
                      const Icone = m.icone;
                      return (
                        <Badge key={m.id} variant="outline" className="flex items-center gap-1">
                          <Icone className="w-3 h-3" />
                          {m.titulo}
                        </Badge>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Tab FAQ */}
        <TabsContent value="faq" className="mt-6">
          <div className="space-y-4">
            {faqFiltrado.map((item, index) => (
              <Card key={index}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-[#004587]" />
                    {item.pergunta}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-600">{item.resposta}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Contato/Suporte */}
      <Card className="bg-slate-50">
        <CardContent className="p-6">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-[#004587]" />
            Ainda precisa de ajuda?
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
              <Mail className="w-8 h-8 text-blue-600" />
              <div>
                <p className="font-medium text-sm">Email</p>
                <p className="text-xs text-slate-500">suporte@fieb.org.br</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
              <Phone className="w-8 h-8 text-green-600" />
              <div>
                <p className="font-medium text-sm">Ramal</p>
                <p className="text-xs text-slate-500">3879-8200</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border">
              <Zap className="w-8 h-8 text-yellow-600" />
              <div>
                <p className="font-medium text-sm">TI - NDSI</p>
                <p className="text-xs text-slate-500">Chamado via SGC</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
