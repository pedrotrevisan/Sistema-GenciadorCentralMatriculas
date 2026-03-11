import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import api from '../services/api';
import {
  GraduationCap,
  Users,
  FileText,
  DollarSign,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  BarChart3,
  Target,
  Zap,
  ArrowRight,
  Maximize2,
  Minimize2,
  RefreshCw,
  Ticket,
  Building2
} from 'lucide-react';

export default function ApresentacaoPage() {
  const [dados, setDados] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [slideAtual, setSlideAtual] = useState(0);

  const carregarDados = async () => {
    try {
      setLoading(true);
      
      // Tentar carregar com token se existir
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      // Se não tem token, usar dados estáticos de demonstração
      if (!token) {
        setDados({
          pedidos: { total: 414, por_status: { realizado: 0, aprovado: 396, em_analise: 1, pendente: 16, documentacao_pendente: 0, cancelado: 1 } },
          vagas: { 
            resumo: { total_turmas: 10, total_vagas: 420, total_ocupadas: 376, vagas_disponiveis: 44, percentual_ocupacao: 89.5, turmas_lotando: 6 },
            por_curso: [
              { curso: 'Técnico em Mecânica', vagas_totais: 42, vagas_ocupadas: 46, percentual: 109.5 },
              { curso: 'Técnico em Redes de Computadores', vagas_totais: 42, vagas_ocupadas: 46, percentual: 109.5 },
              { curso: 'Técnico em Manutenção Automotiva', vagas_totais: 42, vagas_ocupadas: 42, percentual: 100 },
              { curso: 'Técnico em Petroquímica', vagas_totais: 42, vagas_ocupadas: 40, percentual: 95.2 },
              { curso: 'Técnico em Mecatrônica', vagas_totais: 42, vagas_ocupadas: 39, percentual: 92.9 },
              { curso: 'Técnico em Eletrotécnica', vagas_totais: 42, vagas_ocupadas: 38, percentual: 90.5 },
              { curso: 'Técnico em Desenvolvimento de Sistemas', vagas_totais: 42, vagas_ocupadas: 37, percentual: 88.1 },
              { curso: 'Técnico em Logística', vagas_totais: 42, vagas_ocupadas: 34, percentual: 81.0 },
              { curso: 'Técnico em Multimídia', vagas_totais: 42, vagas_ocupadas: 29, percentual: 69.0 },
              { curso: 'Técnico em Biotecnologia', vagas_totais: 42, vagas_ocupadas: 25, percentual: 59.5 }
            ]
          },
          reembolsos: { total: 50, total_aberto: 20, total_aguardando: 0, total_enviado: 5, total_pago: 25 },
          pendencias: { total_pendente: 0, total_aguardando: 0, total_em_analise: 0, total_reenvio: 0, total_aprovado: 414 }
        });
        setLoading(false);
        return;
      }

      const [pedidos, vagas, reembolsos, pendencias] = await Promise.all([
        api.get('/pedidos/analytics', { headers }).catch(() => ({ data: {} })),
        api.get('/painel-vagas/dashboard', { headers }).catch(() => ({ data: { resumo: {} } })),
        api.get('/reembolsos/dashboard', { headers }).catch(() => ({ data: {} })),
        api.get('/pendencias/dashboard', { headers }).catch(() => ({ data: {} }))
      ]);

      setDados({
        pedidos: pedidos.data,
        vagas: vagas.data,
        reembolsos: reembolsos.data,
        pendencias: pendencias.data
      });
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      // Fallback para dados de demonstração
      setDados({
        pedidos: { total: 414 },
        vagas: { resumo: { total_turmas: 10, total_vagas: 420, total_ocupadas: 376, vagas_disponiveis: 44, percentual_ocupacao: 89.5, turmas_lotando: 6 }, por_curso: [] },
        reembolsos: { total: 50 },
        pendencias: { total_pendente: 8 }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarDados();
    // Auto refresh a cada 30 segundos
    const interval = setInterval(carregarDados, 30000);
    return () => clearInterval(interval);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setFullscreen(true);
    } else {
      document.exitFullscreen();
      setFullscreen(false);
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') {
        setSlideAtual(prev => Math.min(prev + 1, 3));
      } else if (e.key === 'ArrowLeft') {
        setSlideAtual(prev => Math.max(prev - 1, 0));
      } else if (e.key === 'f' || e.key === 'F') {
        toggleFullscreen();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  if (loading || !dados) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-t-transparent mx-auto mb-4"></div>
          <p className="text-white text-xl">Carregando dados...</p>
        </div>
      </div>
    );
  }

  const vagas = dados.vagas?.resumo || {};
  const porCurso = dados.vagas?.por_curso || [];

  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white ${fullscreen ? 'p-8' : 'p-4'}`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3">
            <img 
              src="https://customer-assets.emergentagent.com/job_matricula-hub/artifacts/p7o5gy77_logo_cimatec.jpg" 
              alt="SENAI CIMATEC"
              className="h-10 object-contain"
            />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-blue-300 bg-clip-text text-transparent">
              SYNAPSE
            </h1>
            <p className="text-blue-300 text-sm">Hub de Inteligência Operacional</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={carregarDados}
            className="text-white hover:bg-white/10"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Atualizar
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={toggleFullscreen}
            className="text-white hover:bg-white/10"
          >
            {fullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </Button>
          <Badge className="bg-green-500/20 text-green-300 border border-green-500/30">
            <span className="animate-pulse mr-2">●</span> Ao Vivo
          </Badge>
        </div>
      </div>

      {/* Navigation Dots */}
      <div className="flex justify-center gap-2 mb-6">
        {[0, 1, 2, 3].map(i => (
          <button
            key={i}
            onClick={() => setSlideAtual(i)}
            className={`w-3 h-3 rounded-full transition-all ${slideAtual === i ? 'bg-white w-8' : 'bg-white/30'}`}
          />
        ))}
      </div>

      {/* Slide 0: Visão Geral */}
      {slideAtual === 0 && (
        <div className="animate-fadeIn">
          <h2 className="text-2xl font-semibold text-center mb-8 text-blue-200">
            Visão Geral do Sistema
          </h2>
          
          {/* Big Numbers */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
            <Card className="bg-white/10 backdrop-blur-sm border-white/20 hover:bg-white/15 transition-all hover:scale-105">
              <CardContent className="p-6 text-center">
                <FileText className="h-10 w-10 mx-auto mb-3 text-blue-400" />
                <p className="text-5xl font-bold text-white mb-2">{dados.pedidos?.total || 414}</p>
                <p className="text-blue-300">Matrículas</p>
              </CardContent>
            </Card>
            
            <Card className="bg-white/10 backdrop-blur-sm border-white/20 hover:bg-white/15 transition-all hover:scale-105">
              <CardContent className="p-6 text-center">
                <GraduationCap className="h-10 w-10 mx-auto mb-3 text-emerald-400" />
                <p className="text-5xl font-bold text-white mb-2">{vagas.total_turmas || 11}</p>
                <p className="text-emerald-300">Turmas Ativas</p>
              </CardContent>
            </Card>
            
            <Card className="bg-white/10 backdrop-blur-sm border-white/20 hover:bg-white/15 transition-all hover:scale-105">
              <CardContent className="p-6 text-center">
                <DollarSign className="h-10 w-10 mx-auto mb-3 text-amber-400" />
                <p className="text-5xl font-bold text-white mb-2">{dados.reembolsos?.total || 50}</p>
                <p className="text-amber-300">Reembolsos</p>
              </CardContent>
            </Card>
            
            <Card className="bg-white/10 backdrop-blur-sm border-white/20 hover:bg-white/15 transition-all hover:scale-105">
              <CardContent className="p-6 text-center">
                <AlertCircle className="h-10 w-10 mx-auto mb-3 text-orange-400" />
                <p className="text-5xl font-bold text-white mb-2">{dados.pendencias?.total_pendente || 0}</p>
                <p className="text-orange-300">Pendências</p>
              </CardContent>
            </Card>
          </div>

          {/* Módulos */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: BarChart3, label: 'Dashboards', desc: 'BI, SLA, Produtividade', color: 'from-blue-500 to-blue-600' },
              { icon: Target, label: 'Kanban', desc: 'Fluxo Visual', color: 'from-purple-500 to-purple-600' },
              { icon: Ticket, label: 'Chamados SGC', desc: 'Demandas BMP', color: 'from-pink-500 to-pink-600' },
              { icon: Zap, label: 'Assistente TOTVS', desc: 'Automação ERP', color: 'from-amber-500 to-amber-600' },
              { icon: Users, label: 'Painel de Vagas', desc: 'Ocupação Visual', color: 'from-emerald-500 to-emerald-600' },
              { icon: FileText, label: 'Pendências', desc: 'Docs. Alunos', color: 'from-orange-500 to-orange-600' },
              { icon: TrendingUp, label: 'Reembolsos', desc: 'Controle Financeiro', color: 'from-green-500 to-green-600' },
              { icon: AlertCircle, label: 'Central Alertas', desc: 'Retornos Atrasados', color: 'from-red-500 to-red-600' },
            ].map((modulo, idx) => (
              <div key={idx} className={`bg-gradient-to-br ${modulo.color} rounded-xl p-4 hover:scale-105 transition-all`}>
                <modulo.icon className="h-8 w-8 mb-2 opacity-80" />
                <p className="font-semibold">{modulo.label}</p>
                <p className="text-sm opacity-80">{modulo.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Slide 1: Painel de Vagas */}
      {slideAtual === 1 && (
        <div className="animate-fadeIn">
          <h2 className="text-2xl font-semibold text-center mb-6 text-blue-200">
            <GraduationCap className="inline h-8 w-8 mr-2" />
            Painel de Vagas - Escola Técnica 2026.1
          </h2>

          {/* KPIs */}
          <div className="grid grid-cols-3 md:grid-cols-6 gap-4 mb-8">
            <Card className="bg-blue-500/20 border-blue-500/30">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{vagas.total_turmas || 11}</p>
                <p className="text-xs text-blue-300">Turmas</p>
              </CardContent>
            </Card>
            <Card className="bg-emerald-500/20 border-emerald-500/30">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{vagas.total_vagas || 438}</p>
                <p className="text-xs text-emerald-300">Total Vagas</p>
              </CardContent>
            </Card>
            <Card className="bg-purple-500/20 border-purple-500/30">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{vagas.total_ocupadas || 410}</p>
                <p className="text-xs text-purple-300">Ocupadas</p>
              </CardContent>
            </Card>
            <Card className="bg-green-500/20 border-green-500/30">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{vagas.vagas_disponiveis || 28}</p>
                <p className="text-xs text-green-300">Disponíveis</p>
              </CardContent>
            </Card>
            <Card className="bg-amber-500/20 border-amber-500/30">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{vagas.percentual_ocupacao || 93.6}%</p>
                <p className="text-xs text-amber-300">Ocupação</p>
              </CardContent>
            </Card>
            <Card className="bg-red-500/20 border-red-500/30">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{vagas.turmas_lotando || 7}</p>
                <p className="text-xs text-red-300">Lotando</p>
              </CardContent>
            </Card>
          </div>

          {/* Barras de Ocupação */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {porCurso.slice(0, 8).map((curso, idx) => {
              const isLotado = curso.percentual >= 100;
              const isLotando = curso.percentual >= 85;
              return (
                <div key={idx} className="bg-white/5 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium truncate max-w-[60%]">{curso.curso}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400">
                        {curso.vagas_ocupadas}/{curso.vagas_totais}
                      </span>
                      {isLotado && <Badge className="bg-red-500 text-xs">LOTADO</Badge>}
                      {!isLotado && isLotando && <Badge className="bg-amber-500 text-xs">LOTANDO</Badge>}
                    </div>
                  </div>
                  <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-1000 ${isLotado ? 'bg-red-500' : isLotando ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={{ width: `${Math.min(curso.percentual, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Slide 2: Matrículas e Pendências */}
      {slideAtual === 2 && (
        <div className="animate-fadeIn">
          <h2 className="text-2xl font-semibold text-center mb-6 text-blue-200">
            <FileText className="inline h-8 w-8 mr-2" />
            Gestão de Matrículas
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Status das Matrículas */}
            <Card className="bg-white/10 backdrop-blur-sm border-white/20">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-emerald-400" />
                  Status das Matrículas
                </h3>
                <div className="space-y-3">
                  {[
                    { label: 'Realizadas', value: dados.pedidos?.por_status?.realizado || 0, color: 'bg-emerald-500' },
                    { label: 'Aprovadas', value: dados.pedidos?.por_status?.aprovado || 0, color: 'bg-green-500' },
                    { label: 'Em Análise', value: dados.pedidos?.por_status?.em_analise || 0, color: 'bg-blue-500' },
                    { label: 'Pendentes', value: dados.pedidos?.por_status?.pendente || 0, color: 'bg-amber-500' },
                    { label: 'Doc. Pendente', value: dados.pedidos?.por_status?.documentacao_pendente || 0, color: 'bg-orange-500' },
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                        <span className="text-sm">{item.label}</span>
                      </div>
                      <span className="font-bold text-lg">{item.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Pendências Documentais */}
            <Card className="bg-white/10 backdrop-blur-sm border-white/20">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-orange-400" />
                  Central de Pendências
                </h3>
                <div className="space-y-3">
                  {[
                    { label: 'Pendentes', value: dados.pendencias?.total_pendente || 0, color: 'bg-amber-500' },
                    { label: 'Aguardando Aluno', value: dados.pendencias?.total_aguardando || 0, color: 'bg-blue-500' },
                    { label: 'Em Análise', value: dados.pendencias?.total_em_analise || 0, color: 'bg-purple-500' },
                    { label: 'Reenvio Necessário', value: dados.pendencias?.total_reenvio || 0, color: 'bg-orange-500' },
                    { label: 'Aprovados', value: dados.pendencias?.total_aprovado || 0, color: 'bg-emerald-500' },
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                        <span className="text-sm">{item.label}</span>
                      </div>
                      <span className="font-bold text-lg">{item.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Reembolsos */}
          <Card className="bg-white/10 backdrop-blur-sm border-white/20 mt-6">
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-400" />
                Reembolsos
              </h3>
              <div className="grid grid-cols-5 gap-4 text-center">
                <div>
                  <p className="text-3xl font-bold text-amber-400">{dados.reembolsos?.total_aberto || 20}</p>
                  <p className="text-xs text-slate-400">Abertos</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-blue-400">{dados.reembolsos?.total_aguardando || 0}</p>
                  <p className="text-xs text-slate-400">Aguardando</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-purple-400">{dados.reembolsos?.total_enviado || 0}</p>
                  <p className="text-xs text-slate-400">Financeiro</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-emerald-400">{dados.reembolsos?.total_pago || 25}</p>
                  <p className="text-xs text-slate-400">Pagos</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-white">{dados.reembolsos?.total || 50}</p>
                  <p className="text-xs text-slate-400">Total</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Slide 3: Benefícios */}
      {slideAtual === 3 && (
        <div className="animate-fadeIn">
          <h2 className="text-2xl font-semibold text-center mb-8 text-blue-200">
            <Zap className="inline h-8 w-8 mr-2" />
            Antes vs Depois do SYNAPSE
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Antes */}
            <Card className="bg-red-500/10 border-red-500/30">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold text-red-400 mb-4 flex items-center gap-2">
                  <span className="text-2xl">😰</span> Antes (Planilhas)
                </h3>
                <ul className="space-y-3">
                  {[
                    'Contar vagas linha por linha',
                    'Anotar pendências no Excel',
                    'Alimentar PowerBI manualmente',
                    'Buscar status em várias abas',
                    'Sem histórico de contatos',
                    'Retrabalho constante'
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-red-300">
                      <span className="text-red-500">✗</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Depois */}
            <Card className="bg-emerald-500/10 border-emerald-500/30">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold text-emerald-400 mb-4 flex items-center gap-2">
                  <span className="text-2xl">🚀</span> Agora (SYNAPSE)
                </h3>
                <ul className="space-y-3">
                  {[
                    'Painel visual de ocupação',
                    'Central de Pendências integrada',
                    'Dashboards em tempo real',
                    'Kanban com drag & drop',
                    'Histórico completo de interações',
                    'Tudo em um só lugar'
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-emerald-300">
                      <span className="text-emerald-500">✓</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Call to Action */}
          <div className="text-center mt-10">
            <div className="inline-block bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl p-8">
              <h3 className="text-2xl font-bold mb-2">Pronto para Produção</h3>
              <p className="text-blue-200 mb-4">414 matrículas • 50 reembolsos • 10 turmas • ~90% ocupação</p>
              <div className="flex justify-center gap-4">
                <Badge className="bg-white/20 text-white text-lg px-4 py-2">
                  <Building2 className="h-4 w-4 mr-2 inline" />
                  SENAI CIMATEC
                </Badge>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer Navigation */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 flex items-center gap-4">
        <Button
          variant="ghost"
          onClick={() => setSlideAtual(prev => Math.max(prev - 1, 0))}
          disabled={slideAtual === 0}
          className="text-white hover:bg-white/10 disabled:opacity-30"
        >
          ← Anterior
        </Button>
        <span className="text-white/50 text-sm">
          {slideAtual + 1} / 4
        </span>
        <Button
          variant="ghost"
          onClick={() => setSlideAtual(prev => Math.min(prev + 1, 3))}
          disabled={slideAtual === 3}
          className="text-white hover:bg-white/10 disabled:opacity-30"
        >
          Próximo →
        </Button>
      </div>

      {/* Keyboard hint */}
      <div className="fixed bottom-6 right-6 text-white/30 text-xs">
        Use ← → para navegar | F para tela cheia
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out;
        }
      `}</style>
    </div>
  );
}
