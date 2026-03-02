import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Checkbox } from '../components/ui/checkbox';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import api from '../services/api';
import {
  Copy, Check, User, MapPin, FileText, Users, Settings,
  ChevronRight, ChevronLeft, Search, RefreshCw, ClipboardList,
  CheckCircle2, Circle, ArrowRight, Home, Building, Phone, Mail,
  Calendar, CreditCard, Shield, Clipboard, ExternalLink
} from 'lucide-react';
import { cn } from '../lib/utils';

// Componente de campo copiável
const CampoCopiavel = ({ label, valor, formato, small = false }) => {
  const [copiado, setCopiado] = useState(false);

  const copiar = () => {
    if (!valor) return;
    navigator.clipboard.writeText(valor);
    setCopiado(true);
    toast.success(`${label} copiado!`);
    setTimeout(() => setCopiado(false), 2000);
  };

  if (!valor) return null;

  return (
    <div className={cn(
      "flex items-center justify-between p-2 rounded-lg border bg-white hover:bg-slate-50 transition-colors",
      small ? "py-1.5" : "py-2"
    )}>
      <div className="flex-1 min-w-0">
        <p className={cn("text-slate-500", small ? "text-xs" : "text-xs")}>{label}</p>
        <p className={cn("font-medium text-slate-800 truncate", small ? "text-sm" : "text-sm")}>
          {formato || valor}
        </p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={copiar}
        className={cn(
          "ml-2 h-8 w-8 p-0 shrink-0",
          copiado && "text-green-600"
        )}
      >
        {copiado ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
      </Button>
    </div>
  );
};

// Componente de item do checklist
const ChecklistItem = ({ id, label, checked, onToggle, subItems = [] }) => {
  return (
    <div className="space-y-1">
      <div 
        className={cn(
          "flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all",
          checked ? "bg-green-50 border border-green-200" : "bg-white border border-slate-200 hover:border-slate-300"
        )}
        onClick={() => onToggle(id)}
      >
        <div className={cn(
          "w-5 h-5 rounded-full flex items-center justify-center shrink-0",
          checked ? "bg-green-500 text-white" : "border-2 border-slate-300"
        )}>
          {checked && <Check className="w-3 h-3" />}
        </div>
        <span className={cn(
          "flex-1 text-sm",
          checked ? "text-green-700 line-through" : "text-slate-700"
        )}>
          {label}
        </span>
      </div>
      {subItems.length > 0 && (
        <div className="ml-8 space-y-1">
          {subItems.map((sub, idx) => (
            <div key={idx} className="text-xs text-slate-500 flex items-center gap-2">
              <Circle className="w-2 h-2" />
              {sub}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const AssistenteTOTVSPage = () => {
  const { pedidoId, alunoIndex } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [pedido, setPedido] = useState(null);
  const [aluno, setAluno] = useState(null);
  const [abaAtiva, setAbaAtiva] = useState('identificacao');
  const [buscaPedido, setBuscaPedido] = useState('');
  
  // Checklist state
  const [checklist, setChecklist] = useState({
    // Identificação
    cpf: false,
    email: false,
    nome: false,
    dataNasc: false,
    sexo: false,
    estadoCivil: false,
    nacionalidade: false,
    corRaca: false,
    grauInstrucao: false,
    // Endereço
    cep: false,
    logradouro: false,
    bairro: false,
    cidade: false,
    telefone: false,
    // Documentos
    rg: false,
    // Responsáveis
    filiacao: false,
    respFinanceiro: false,
    // Diversos
    ensinoBasico: false,
    // Final
    salvar: false
  });

  useEffect(() => {
    if (pedidoId) {
      carregarPedido(pedidoId);
    } else {
      setLoading(false);
    }
  }, [pedidoId, alunoIndex]);

  const carregarPedido = async (id) => {
    setLoading(true);
    try {
      const response = await api.get(`/pedidos/${id}`);
      setPedido(response.data);
      
      // Selecionar aluno pelo índice ou primeiro
      const idx = parseInt(alunoIndex) || 0;
      if (response.data.alunos && response.data.alunos.length > idx) {
        setAluno(response.data.alunos[idx]);
      } else if (response.data.alunos && response.data.alunos.length > 0) {
        setAluno(response.data.alunos[0]);
      }
    } catch (error) {
      toast.error('Erro ao carregar pedido');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const buscarPedido = () => {
    if (!buscaPedido.trim()) {
      toast.error('Digite o ID ou protocolo do pedido');
      return;
    }
    navigate(`/assistente-totvs/${buscaPedido.trim()}`);
  };

  const toggleChecklist = (id) => {
    setChecklist(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const calcularProgresso = () => {
    const total = Object.keys(checklist).length;
    const completos = Object.values(checklist).filter(Boolean).length;
    return Math.round((completos / total) * 100);
  };

  const formatarCPF = (cpf) => {
    if (!cpf) return '';
    const nums = cpf.replace(/\D/g, '');
    return nums.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  };

  const formatarTelefone = (tel) => {
    if (!tel) return '';
    const nums = tel.replace(/\D/g, '');
    if (nums.length === 11) {
      return nums.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    }
    return nums.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  };

  const formatarData = (data) => {
    if (!data) return '';
    try {
      const d = new Date(data);
      return d.toLocaleDateString('pt-BR');
    } catch {
      return data;
    }
  };

  const formatarNome = (nome) => {
    if (!nome) return '';
    return nome
      .toLowerCase()
      .split(' ')
      .map(p => p.charAt(0).toUpperCase() + p.slice(1))
      .join(' ');
  };

  const progresso = calcularProgresso();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  // Tela de busca se não tiver pedido
  if (!pedido) {
    return (
      <div className="max-w-2xl mx-auto space-y-6" data-testid="assistente-totvs-busca">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Assistente TOTVS</h1>
          <p className="text-slate-500">
            Cole dados formatados e siga o checklist para não perder o fio
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5 text-blue-600" />
              Buscar Pedido
            </CardTitle>
            <CardDescription>
              Digite o ID ou número de protocolo do pedido para começar
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <Input
                placeholder="ID ou protocolo (ex: CM-2026-0001)"
                value={buscaPedido}
                onChange={(e) => setBuscaPedido(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && buscarPedido()}
                className="flex-1"
                data-testid="input-busca-pedido-totvs"
              />
              <Button onClick={buscarPedido}>
                <Search className="w-4 h-4 mr-2" />
                Buscar
              </Button>
            </div>
          </CardContent>
        </Card>

        <Alert className="bg-blue-50 border-blue-200">
          <ClipboardList className="w-4 h-4 text-blue-600" />
          <AlertDescription className="text-blue-700">
            <strong>Dica:</strong> Você também pode acessar o Assistente TOTVS diretamente 
            da página de detalhes do pedido, clicando no botão "Abrir Assistente TOTVS".
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="assistente-totvs-page">
      {/* Header com progresso */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Assistente TOTVS</h1>
          <p className="text-slate-500">
            Pedido: {pedido.numero_protocolo || pedido.id?.substring(0, 8)}
            {aluno && ` • ${formatarNome(aluno.nome)}`}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-slate-500">Progresso</p>
            <p className="text-2xl font-bold text-blue-600">{progresso}%</p>
          </div>
          <div className="w-24">
            <Progress value={progresso} className="h-3" />
          </div>
        </div>
      </div>

      {/* Seletor de alunos se houver mais de um */}
      {pedido.alunos && pedido.alunos.length > 1 && (
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="py-3">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-amber-700 font-medium">Alunos:</span>
              {pedido.alunos.map((a, idx) => (
                <Button
                  key={idx}
                  variant={aluno === a ? "default" : "outline"}
                  size="sm"
                  onClick={() => setAluno(a)}
                  className={cn(
                    "h-7",
                    aluno === a ? "bg-amber-600 hover:bg-amber-700" : ""
                  )}
                >
                  {formatarNome(a.nome?.split(' ')[0])}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Coluna da esquerda - Dados para copiar */}
        <div className="lg:col-span-2 space-y-4">
          <Tabs value={abaAtiva} onValueChange={setAbaAtiva}>
            <TabsList className="grid grid-cols-5 w-full">
              <TabsTrigger value="identificacao" className="text-xs">
                <User className="w-3 h-3 mr-1" />
                Identificação
              </TabsTrigger>
              <TabsTrigger value="endereco" className="text-xs">
                <MapPin className="w-3 h-3 mr-1" />
                Endereço
              </TabsTrigger>
              <TabsTrigger value="documentos" className="text-xs">
                <FileText className="w-3 h-3 mr-1" />
                Documentos
              </TabsTrigger>
              <TabsTrigger value="responsaveis" className="text-xs">
                <Users className="w-3 h-3 mr-1" />
                Responsáveis
              </TabsTrigger>
              <TabsTrigger value="diversos" className="text-xs">
                <Settings className="w-3 h-3 mr-1" />
                Diversos
              </TabsTrigger>
            </TabsList>

            {/* Aba Identificação */}
            <TabsContent value="identificacao" className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <User className="w-4 h-4 text-blue-600" />
                    Dados Básicos
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Preencha primeiro: CPF → Email → Nome → Data Nasc → Sexo
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CampoCopiavel 
                    label="CPF" 
                    valor={aluno?.cpf}
                    formato={formatarCPF(aluno?.cpf)}
                  />
                  <CampoCopiavel 
                    label="E-mail" 
                    valor={aluno?.email}
                  />
                  <CampoCopiavel 
                    label="Nome Completo" 
                    valor={aluno?.nome}
                    formato={formatarNome(aluno?.nome)}
                  />
                  <CampoCopiavel 
                    label="Data de Nascimento" 
                    valor={aluno?.data_nascimento}
                    formato={formatarData(aluno?.data_nascimento)}
                  />
                  <CampoCopiavel 
                    label="Sexo" 
                    valor={aluno?.sexo}
                  />
                  <CampoCopiavel 
                    label="Estado Civil" 
                    valor={aluno?.estado_civil || "Solteiro(a)"}
                  />
                  <CampoCopiavel 
                    label="Nacionalidade" 
                    valor="Brasileiro(a)"
                  />
                  <CampoCopiavel 
                    label="Naturalidade" 
                    valor={aluno?.naturalidade}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Informações Adicionais</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CampoCopiavel 
                    label="Cor/Raça" 
                    valor={aluno?.cor_raca}
                  />
                  <CampoCopiavel 
                    label="Grau de Instrução" 
                    valor={aluno?.escolaridade}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Aba Endereço */}
            <TabsContent value="endereco" className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Home className="w-4 h-4 text-green-600" />
                    Endereço Residencial
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CampoCopiavel 
                    label="CEP" 
                    valor={aluno?.cep}
                  />
                  <CampoCopiavel 
                    label="Logradouro" 
                    valor={aluno?.endereco}
                  />
                  <CampoCopiavel 
                    label="Número" 
                    valor={aluno?.numero}
                  />
                  <CampoCopiavel 
                    label="Complemento" 
                    valor={aluno?.complemento}
                  />
                  <CampoCopiavel 
                    label="Bairro" 
                    valor={aluno?.bairro}
                  />
                  <CampoCopiavel 
                    label="Cidade" 
                    valor={aluno?.cidade}
                  />
                  <CampoCopiavel 
                    label="Estado" 
                    valor={aluno?.estado}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Phone className="w-4 h-4 text-blue-600" />
                    Contatos
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CampoCopiavel 
                    label="Telefone I" 
                    valor={aluno?.telefone}
                    formato={formatarTelefone(aluno?.telefone)}
                  />
                  <CampoCopiavel 
                    label="Telefone II" 
                    valor={aluno?.telefone2}
                    formato={formatarTelefone(aluno?.telefone2)}
                  />
                  <CampoCopiavel 
                    label="Email Pessoal" 
                    valor={aluno?.email}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Aba Documentos */}
            <TabsContent value="documentos" className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <CreditCard className="w-4 h-4 text-purple-600" />
                    Identificação Geral
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CampoCopiavel 
                    label="CPF" 
                    valor={aluno?.cpf}
                    formato={formatarCPF(aluno?.cpf)}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Shield className="w-4 h-4 text-amber-600" />
                    Carteira de Identidade (RG)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CampoCopiavel 
                    label="Número RG" 
                    valor={aluno?.rg}
                  />
                  <CampoCopiavel 
                    label="Data Emissão" 
                    valor={aluno?.rg_emissao}
                    formato={formatarData(aluno?.rg_emissao)}
                  />
                  <CampoCopiavel 
                    label="Órgão Emissor" 
                    valor={aluno?.rg_orgao}
                  />
                  <CampoCopiavel 
                    label="Estado Emissor" 
                    valor={aluno?.rg_estado || aluno?.estado}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Aba Responsáveis */}
            <TabsContent value="responsaveis" className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Users className="w-4 h-4 text-indigo-600" />
                    Filiação
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CampoCopiavel 
                    label="Nome da Mãe" 
                    valor={aluno?.nome_mae}
                    formato={formatarNome(aluno?.nome_mae)}
                  />
                  <CampoCopiavel 
                    label="Nome do Pai" 
                    valor={aluno?.nome_pai}
                    formato={formatarNome(aluno?.nome_pai)}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Responsável Financeiro</CardTitle>
                  <CardDescription className="text-xs">
                    Clique em "Cadastrar ALUNO como responsável" se for maior de idade
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Alert className="bg-blue-50 border-blue-200">
                    <AlertDescription className="text-blue-700 text-sm">
                      Para alunos maiores de 18 anos, use o botão 
                      <strong> "Cadastrar ALUNO como responsável"</strong> no TOTVS.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Aba Diversos */}
            <TabsContent value="diversos" className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Building className="w-4 h-4 text-teal-600" />
                    Ensino Básico
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Preencha para evitar críticas posteriores no TOTVS
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <CampoCopiavel 
                    label="Instituição" 
                    valor={aluno?.instituicao_ensino || "Não Informado"}
                  />
                  <CampoCopiavel 
                    label="Grau" 
                    valor={aluno?.escolaridade || aluno?.grau_instrucao}
                  />
                  <CampoCopiavel 
                    label="Ano de Conclusão" 
                    valor={aluno?.ano_conclusao}
                  />
                  
                  <Alert className="bg-amber-50 border-amber-200 mt-3">
                    <AlertDescription className="text-amber-700 text-xs">
                      <strong>Dica:</strong> Se não tiver a informação exata, use valores padrão 
                      para evitar críticas: Instituição = "Não Informado", Grau = conforme escolaridade.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Coluna da direita - Checklist */}
        <div className="space-y-4">
          <Card className="sticky top-4">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <ClipboardList className="w-4 h-4 text-green-600" />
                Checklist TOTVS
              </CardTitle>
              <CardDescription className="text-xs">
                Marque cada item conforme preenche no TOTVS
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Identificação */}
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1">
                  <User className="w-3 h-3" /> ABA: IDENTIFICAÇÃO
                </p>
                <div className="space-y-1">
                  <ChecklistItem 
                    id="cpf" 
                    label="CPF" 
                    checked={checklist.cpf}
                    onToggle={toggleChecklist}
                  />
                  <ChecklistItem 
                    id="email" 
                    label="E-mail" 
                    checked={checklist.email}
                    onToggle={toggleChecklist}
                  />
                  <ChecklistItem 
                    id="nome" 
                    label="Nome completo" 
                    checked={checklist.nome}
                    onToggle={toggleChecklist}
                  />
                  <ChecklistItem 
                    id="dataNasc" 
                    label="Data de nascimento" 
                    checked={checklist.dataNasc}
                    onToggle={toggleChecklist}
                  />
                  <ChecklistItem 
                    id="sexo" 
                    label="Sexo" 
                    checked={checklist.sexo}
                    onToggle={toggleChecklist}
                  />
                </div>
              </div>

              <Separator />

              {/* Endereço */}
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1">
                  <MapPin className="w-3 h-3" /> ABA: ENDEREÇO
                </p>
                <div className="space-y-1">
                  <ChecklistItem 
                    id="cep" 
                    label="CEP + Endereço" 
                    checked={checklist.cep}
                    onToggle={toggleChecklist}
                  />
                  <ChecklistItem 
                    id="telefone" 
                    label="Telefones" 
                    checked={checklist.telefone}
                    onToggle={toggleChecklist}
                  />
                </div>
              </div>

              <Separator />

              {/* Documentos */}
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1">
                  <FileText className="w-3 h-3" /> ABA: DOCUMENTOS
                </p>
                <div className="space-y-1">
                  <ChecklistItem 
                    id="rg" 
                    label="RG completo" 
                    checked={checklist.rg}
                    onToggle={toggleChecklist}
                  />
                </div>
              </div>

              <Separator />

              {/* Responsáveis */}
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1">
                  <Users className="w-3 h-3" /> ABA: RESPONSÁVEIS
                </p>
                <div className="space-y-1">
                  <ChecklistItem 
                    id="filiacao" 
                    label="Filiação (Mãe/Pai)" 
                    checked={checklist.filiacao}
                    onToggle={toggleChecklist}
                  />
                  <ChecklistItem 
                    id="respFinanceiro" 
                    label="Responsável financeiro" 
                    checked={checklist.respFinanceiro}
                    onToggle={toggleChecklist}
                  />
                </div>
              </div>

              <Separator />

              {/* Diversos */}
              <div>
                <p className="text-xs font-semibold text-slate-500 mb-2 flex items-center gap-1">
                  <Settings className="w-3 h-3" /> ABA: DIVERSOS
                </p>
                <div className="space-y-1">
                  <ChecklistItem 
                    id="ensinoBasico" 
                    label="Ensino Básico (Instituição/Grau/Ano)" 
                    checked={checklist.ensinoBasico}
                    onToggle={toggleChecklist}
                  />
                </div>
              </div>

              <Separator />

              {/* Final */}
              <ChecklistItem 
                id="salvar" 
                label="SALVAR CADASTRO" 
                checked={checklist.salvar}
                onToggle={toggleChecklist}
              />

              {progresso === 100 && (
                <Alert className="bg-green-50 border-green-200 mt-4">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <AlertDescription className="text-green-700 text-sm">
                    <strong>Parabéns!</strong> Cadastro completo no TOTVS!
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Atalhos */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Atalhos</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button 
                variant="outline" 
                className="w-full justify-start text-sm"
                onClick={() => navigate(`/pedidos/${pedidoId}`)}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Ver pedido completo
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start text-sm"
                onClick={() => {
                  setChecklist(Object.fromEntries(
                    Object.keys(checklist).map(k => [k, false])
                  ));
                  toast.success('Checklist reiniciado!');
                }}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reiniciar checklist
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AssistenteTOTVSPage;
