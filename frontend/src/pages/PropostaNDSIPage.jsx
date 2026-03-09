import React from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  FileText,
  CheckCircle,
  AlertTriangle,
  Zap,
  BarChart3,
  Database,
  Server,
  Code,
  ArrowRight,
  Building2,
  Shield,
  RefreshCw,
  GitBranch,
  Clock,
  Link2
} from 'lucide-react';

export default function PropostaNDSIPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center items-center gap-3 mb-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3">
              <img 
                src="https://customer-assets.emergentagent.com/job_matricula-hub/artifacts/p7o5gy77_logo_cimatec.jpg" 
                alt="SENAI CIMATEC"
                className="h-12 object-contain"
              />
            </div>
          </div>
          <Badge className="bg-blue-500 text-white mb-4">PROPOSTA TÉCNICA</Badge>
          <h1 className="text-3xl font-bold text-white mb-2">
            Integração SYNAPSE ↔ TOTVS
          </h1>
          <p className="text-slate-400">
            Proposta de integração para a Central de Matrículas
          </p>
        </div>

        {/* Para quem */}
        <Card className="mb-6 bg-white/5 border-white/10 text-white">
          <CardContent className="p-4">
            <p className="text-sm">
              <strong className="text-blue-400">Para:</strong> NDSI - Núcleo de Desenvolvimento de Sistemas Internos
            </p>
            <p className="text-sm">
              <strong className="text-blue-400">De:</strong> Pedro Passos - Central de Matrículas CAC
            </p>
            <p className="text-sm">
              <strong className="text-blue-400">Data:</strong> Março/2026
            </p>
          </CardContent>
        </Card>

        {/* Contexto */}
        <Card className="mb-6 bg-white/5 border-white/10 text-white">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-400" />
              Contexto
            </h2>
            <p className="text-slate-300 leading-relaxed mb-4">
              A equipe da Central de Matrículas (CAC) desenvolveu o sistema <strong className="text-white">SYNAPSE</strong>, 
              um Hub de Inteligência Operacional para gestão de matrículas, pendências documentais, 
              reembolsos e controle de vagas.
            </p>
            <p className="text-slate-300 leading-relaxed">
              O sistema já está operacional com <strong className="text-white">413 matrículas</strong>, 
              <strong className="text-white"> 50 reembolsos</strong> e <strong className="text-white">11 turmas</strong> cadastradas, 
              eliminando o uso de planilhas Excel para controle.
            </p>
          </CardContent>
        </Card>

        {/* Stack Técnica */}
        <Card className="mb-6 bg-white/5 border-white/10 text-white">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Code className="h-5 w-5 text-green-400" />
              Stack Técnica do SYNAPSE
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-white/5 rounded-lg">
                <h3 className="font-semibold text-blue-400 mb-2">Backend</h3>
                <ul className="text-sm text-slate-300 space-y-1">
                  <li>• Python 3.11 + FastAPI</li>
                  <li>• SQLite (pode migrar para PostgreSQL)</li>
                  <li>• SQLAlchemy ORM</li>
                  <li>• Autenticação JWT</li>
                  <li>• API RESTful documentada</li>
                </ul>
              </div>
              <div className="p-4 bg-white/5 rounded-lg">
                <h3 className="font-semibold text-green-400 mb-2">Frontend</h3>
                <ul className="text-sm text-slate-300 space-y-1">
                  <li>• React 18 + Vite</li>
                  <li>• Tailwind CSS</li>
                  <li>• Shadcn/UI Components</li>
                  <li>• Recharts (gráficos)</li>
                  <li>• React Beautiful DnD (Kanban)</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Solicitação */}
        <Card className="mb-6 bg-gradient-to-r from-blue-900/50 to-purple-900/50 border-blue-500/30 text-white">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Link2 className="h-5 w-5 text-blue-400" />
              Solicitação de Integração
            </h2>
            <p className="text-slate-300 mb-4">
              Para automatizar a importação de dados e eliminar a necessidade de exportação manual 
              do TOTVS, solicitamos uma das seguintes opções de integração:
            </p>
            
            <div className="space-y-4">
              {/* Opção 1 */}
              <div className="p-4 bg-white/5 rounded-lg border border-green-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Badge className="bg-green-500">RECOMENDADA</Badge>
                  <h3 className="font-semibold text-green-400">Opção 1: API REST</h3>
                </div>
                <p className="text-sm text-slate-300 mb-2">
                  Endpoint REST para consulta de matrículas/inscrições do TOTVS
                </p>
                <div className="bg-black/30 rounded p-3 font-mono text-xs text-slate-400">
                  GET /api/totvs/matriculas?status=pendente&periodo=2026.1<br/>
                  Authorization: Bearer [token]
                </div>
              </div>

              {/* Opção 2 */}
              <div className="p-4 bg-white/5 rounded-lg border border-blue-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Badge className="bg-blue-500">IDEAL</Badge>
                  <h3 className="font-semibold text-blue-400">Opção 2: Webhook</h3>
                </div>
                <p className="text-sm text-slate-300 mb-2">
                  TOTVS notifica o SYNAPSE quando há nova inscrição/atualização
                </p>
                <div className="bg-black/30 rounded p-3 font-mono text-xs text-slate-400">
                  POST https://synapse.senai.br/api/webhook/totvs<br/>
                  {`{ "evento": "nova_matricula", "dados": {...} }`}
                </div>
              </div>

              {/* Opção 3 */}
              <div className="p-4 bg-white/5 rounded-lg border border-amber-500/30">
                <div className="flex items-center gap-2 mb-2">
                  <Badge className="bg-amber-500">ALTERNATIVA</Badge>
                  <h3 className="font-semibold text-amber-400">Opção 3: View no Banco</h3>
                </div>
                <p className="text-sm text-slate-300 mb-2">
                  Acesso de leitura a uma view específica no banco do TOTVS
                </p>
                <div className="bg-black/30 rounded p-3 font-mono text-xs text-slate-400">
                  SELECT * FROM vw_matriculas_cac<br/>
                  WHERE dt_inscricao {'>'}= '2026-01-01'
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Dados Necessários */}
        <Card className="mb-6 bg-white/5 border-white/10 text-white">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Database className="h-5 w-5 text-purple-400" />
              Dados Necessários do TOTVS
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-2 text-slate-400">Campo</th>
                    <th className="text-left py-2 text-slate-400">Descrição</th>
                    <th className="text-left py-2 text-slate-400">Tipo</th>
                  </tr>
                </thead>
                <tbody className="text-slate-300">
                  <tr className="border-b border-white/5">
                    <td className="py-2 font-mono text-blue-400">cod_matricula</td>
                    <td>Identificador único</td>
                    <td>string</td>
                  </tr>
                  <tr className="border-b border-white/5">
                    <td className="py-2 font-mono text-blue-400">nome_aluno</td>
                    <td>Nome completo do aluno</td>
                    <td>string</td>
                  </tr>
                  <tr className="border-b border-white/5">
                    <td className="py-2 font-mono text-blue-400">cpf</td>
                    <td>CPF do aluno</td>
                    <td>string</td>
                  </tr>
                  <tr className="border-b border-white/5">
                    <td className="py-2 font-mono text-blue-400">cod_turma</td>
                    <td>Código da turma (ex: B101622)</td>
                    <td>string</td>
                  </tr>
                  <tr className="border-b border-white/5">
                    <td className="py-2 font-mono text-blue-400">nome_curso</td>
                    <td>Nome do curso</td>
                    <td>string</td>
                  </tr>
                  <tr className="border-b border-white/5">
                    <td className="py-2 font-mono text-blue-400">status</td>
                    <td>Status da matrícula</td>
                    <td>enum</td>
                  </tr>
                  <tr className="border-b border-white/5">
                    <td className="py-2 font-mono text-blue-400">dt_inscricao</td>
                    <td>Data de inscrição</td>
                    <td>datetime</td>
                  </tr>
                  <tr className="border-b border-white/5">
                    <td className="py-2 font-mono text-blue-400">vagas_turma</td>
                    <td>Total de vagas da turma</td>
                    <td>integer</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Segurança */}
        <Card className="mb-6 bg-white/5 border-white/10 text-white">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5 text-green-400" />
              Considerações de Segurança
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                { titulo: 'Acesso apenas leitura', desc: 'SYNAPSE não altera dados no TOTVS' },
                { titulo: 'Autenticação', desc: 'Token JWT ou API Key dedicada' },
                { titulo: 'Criptografia', desc: 'HTTPS/TLS em todas as comunicações' },
                { titulo: 'Auditoria', desc: 'Log de todas as consultas realizadas' },
              ].map((item, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-white/5 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-400 mt-0.5" />
                  <div>
                    <p className="font-medium text-white">{item.titulo}</p>
                    <p className="text-sm text-slate-400">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Benefícios */}
        <Card className="mb-6 bg-white/5 border-white/10 text-white">
          <CardContent className="p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-400" />
              Benefícios da Integração
            </h2>
            <div className="space-y-3">
              {[
                { icon: Clock, titulo: 'Eliminação de trabalho manual', desc: 'Sem exportar/importar planilhas' },
                { icon: RefreshCw, titulo: 'Dados sempre atualizados', desc: 'Sincronização automática' },
                { icon: GitBranch, titulo: 'Fonte única de verdade', desc: 'TOTVS como master, SYNAPSE como visualização' },
                { icon: BarChart3, titulo: 'Dashboards em tempo real', desc: 'Métricas atualizadas automaticamente' },
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-4 p-3 bg-white/5 rounded-lg">
                  <item.icon className="h-6 w-6 text-blue-400" />
                  <div>
                    <p className="font-medium text-white">{item.titulo}</p>
                    <p className="text-sm text-slate-400">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Contato */}
        <Card className="mb-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <CardContent className="p-6 text-center">
            <h2 className="text-xl font-bold mb-4">Demonstração do Sistema</h2>
            <p className="text-blue-100 mb-4">
              O sistema está disponível para avaliação técnica:
            </p>
            <div className="space-y-2">
              <p className="text-white font-mono">🔗 hub-senai.preview.emergentagent.com</p>
              <p className="text-sm text-blue-200">Modo Apresentação: /apresentacao</p>
            </div>
            <div className="mt-6 pt-4 border-t border-white/20">
              <p className="text-sm text-blue-200">
                Contato: Pedro Passos | pedro.passos@fieb.org.br
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-slate-500 text-sm">
          <p>Central de Matrículas - CAC</p>
          <p>SENAI CIMATEC 2026</p>
        </div>

      </div>
    </div>
  );
}
