import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { pedidosAPI, auxiliaresAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { toast } from 'sonner';
import { 
  ChevronLeft, 
  ChevronRight, 
  Check, 
  Plus, 
  Trash2, 
  User,
  Building,
  FileText,
  Loader2
} from 'lucide-react';

// Preposições que devem permanecer em minúsculo
const PREPOSICOES = new Set(['da', 'de', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos', 'para', 'por']);

/**
 * Formata nome próprio para Title Case, mantendo preposições em minúsculo.
 * Ex: "PEDRO HENRIQUE DA SILVA" -> "Pedro Henrique da Silva"
 */
const formatarNomeProprio = (nome) => {
  if (!nome) return nome;
  
  return nome
    .trim()
    .toLowerCase()
    .split(' ')
    .map((palavra, index) => {
      // Primeira palavra sempre capitalizada, preposições em minúsculo no meio
      if (index === 0 || !PREPOSICOES.has(palavra)) {
        return palavra.charAt(0).toUpperCase() + palavra.slice(1);
      }
      return palavra;
    })
    .join(' ');
};

/**
 * Formata texto para Title Case simples (todas as palavras capitalizadas)
 */
const formatarTextoTitulo = (texto) => {
  if (!texto) return texto;
  
  return texto
    .trim()
    .toLowerCase()
    .split(' ')
    .map(palavra => palavra.charAt(0).toUpperCase() + palavra.slice(1))
    .join(' ');
};

const ESTADOS_BR = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

const COR_RACA_OPTIONS = [
  'Branca', 'Preta', 'Parda', 'Amarela', 'Indígena', 'Não declarada'
];

const GRAU_INSTRUCAO_OPTIONS = [
  'Fundamental Incompleto',
  'Fundamental Completo',
  'Médio Incompleto',
  'Médio Completo',
  'Superior Incompleto',
  'Superior Completo',
  'Pós-Graduação'
];

const emptyAluno = {
  nome: '',
  cpf: '',
  email: '',
  telefone: '',
  data_nascimento: '',
  rg: '',
  rg_orgao_emissor: '',
  rg_uf: '',
  rg_data_emissao: '',
  naturalidade: '',
  naturalidade_uf: '',
  sexo: '',
  cor_raca: '',
  grau_instrucao: '',
  nome_pai: '',
  nome_mae: '',
  endereco_cep: '',
  endereco_logradouro: '',
  endereco_numero: '',
  endereco_complemento: '',
  endereco_bairro: '',
  endereco_cidade: '',
  endereco_uf: ''
};

const NovaMatriculaPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [buscandoCep, setBuscandoCep] = useState({}); // {alunoIndex: true/false}

  // Dados auxiliares
  const [cursos, setCursos] = useState([]);
  const [projetos, setProjetos] = useState([]);
  const [empresas, setEmpresas] = useState([]);

  // Form data
  const [formData, setFormData] = useState({
    curso_id: '',
    curso_nome: '',
    vinculo_tipo: 'projeto', // 'projeto' ou 'empresa'
    projeto_id: '',
    projeto_nome: '',
    empresa_id: '',
    empresa_nome: '',
    observacoes: '',
    alunos: [{ ...emptyAluno }]
  });

  useEffect(() => {
    fetchDadosAuxiliares();
  }, []);

  const fetchDadosAuxiliares = async () => {
    setLoading(true);
    try {
      const [cursosRes, projetosRes, empresasRes] = await Promise.all([
        auxiliaresAPI.getCursos(),
        auxiliaresAPI.getProjetos(),
        auxiliaresAPI.getEmpresas()
      ]);
      setCursos(cursosRes.data);
      setProjetos(projetosRes.data);
      setEmpresas(empresasRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleCursoChange = (cursoId) => {
    const curso = cursos.find(c => c.id === cursoId);
    setFormData(prev => ({
      ...prev,
      curso_id: cursoId,
      curso_nome: curso?.nome || ''
    }));
  };

  const handleVinculoChange = (tipo) => {
    setFormData(prev => ({
      ...prev,
      vinculo_tipo: tipo,
      projeto_id: '',
      projeto_nome: '',
      empresa_id: '',
      empresa_nome: ''
    }));
  };

  const handleProjetoChange = (projetoId) => {
    const projeto = projetos.find(p => p.id === projetoId);
    setFormData(prev => ({
      ...prev,
      projeto_id: projetoId,
      projeto_nome: projeto?.nome || ''
    }));
  };

  const handleEmpresaChange = (empresaId) => {
    const empresa = empresas.find(e => e.id === empresaId);
    setFormData(prev => ({
      ...prev,
      empresa_id: empresaId,
      empresa_nome: empresa?.nome || ''
    }));
  };

  const handleAlunoChange = (index, field, value) => {
    setFormData(prev => {
      const alunos = [...prev.alunos];
      alunos[index] = { ...alunos[index], [field]: value };
      return { ...prev, alunos };
    });
  };

  // Formata nome quando sai do campo
  const handleNomeBlur = (index) => {
    setFormData(prev => {
      const alunos = [...prev.alunos];
      alunos[index] = { ...alunos[index], nome: formatarNomeProprio(alunos[index].nome) };
      return { ...prev, alunos };
    });
  };

  // Formata campos de endereço quando sai do campo
  const handleEnderecoBlur = (index, field) => {
    setFormData(prev => {
      const alunos = [...prev.alunos];
      alunos[index] = { ...alunos[index], [field]: formatarTextoTitulo(alunos[index][field]) };
      return { ...prev, alunos };
    });
  };

  // Busca endereço pelo CEP usando ViaCEP
  const buscarCep = async (index, cep) => {
    // Remove caracteres não numéricos
    const cepLimpo = cep.replace(/\D/g, '');
    
    // Valida se tem 8 dígitos
    if (cepLimpo.length !== 8) {
      return;
    }
    
    setBuscandoCep(prev => ({ ...prev, [index]: true }));
    
    try {
      const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
      const data = await response.json();
      
      if (data.erro) {
        toast.error('CEP não encontrado');
        return;
      }
      
      // Preenche os campos de endereço
      setFormData(prev => {
        const alunos = [...prev.alunos];
        alunos[index] = {
          ...alunos[index],
          endereco_logradouro: formatarTextoTitulo(data.logradouro) || '',
          endereco_bairro: formatarTextoTitulo(data.bairro) || '',
          endereco_cidade: formatarTextoTitulo(data.localidade) || '',
          endereco_uf: data.uf || ''
        };
        return { ...prev, alunos };
      });
      
      toast.success('Endereço preenchido automaticamente!');
    } catch (error) {
      console.error('Erro ao buscar CEP:', error);
      toast.error('Erro ao buscar CEP. Tente novamente.');
    } finally {
      setBuscandoCep(prev => ({ ...prev, [index]: false }));
    }
  };

  const addAluno = () => {
    setFormData(prev => ({
      ...prev,
      alunos: [...prev.alunos, { ...emptyAluno }]
    }));
  };

  const removeAluno = (index) => {
    if (formData.alunos.length <= 1) {
      toast.error('O pedido deve ter pelo menos 1 aluno');
      return;
    }
    setFormData(prev => ({
      ...prev,
      alunos: prev.alunos.filter((_, i) => i !== index)
    }));
  };

  const validateStep1 = () => {
    if (!formData.curso_id) {
      toast.error('Selecione um curso');
      return false;
    }
    if (formData.vinculo_tipo === 'projeto' && !formData.projeto_id) {
      toast.error('Selecione um projeto');
      return false;
    }
    if (formData.vinculo_tipo === 'empresa' && !formData.empresa_id) {
      toast.error('Selecione uma empresa');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    for (let i = 0; i < formData.alunos.length; i++) {
      const aluno = formData.alunos[i];
      if (!aluno.nome || aluno.nome.length < 3) {
        toast.error(`Aluno ${i + 1}: Nome deve ter pelo menos 3 caracteres`);
        return false;
      }
      if (!aluno.cpf || aluno.cpf.length < 11) {
        toast.error(`Aluno ${i + 1}: CPF inválido`);
        return false;
      }
      if (!aluno.email || !aluno.email.includes('@')) {
        toast.error(`Aluno ${i + 1}: Email inválido`);
        return false;
      }
      if (!aluno.telefone || aluno.telefone.length < 10) {
        toast.error(`Aluno ${i + 1}: Telefone inválido`);
        return false;
      }
      if (!aluno.data_nascimento) {
        toast.error(`Aluno ${i + 1}: Data de nascimento obrigatória`);
        return false;
      }
      if (!aluno.rg) {
        toast.error(`Aluno ${i + 1}: RG obrigatório`);
        return false;
      }
      if (!aluno.endereco_cep || !aluno.endereco_logradouro || !aluno.endereco_numero || !aluno.endereco_bairro || !aluno.endereco_cidade || !aluno.endereco_uf) {
        toast.error(`Aluno ${i + 1}: Preencha o endereço completo`);
        return false;
      }
    }
    return true;
  };

  const nextStep = () => {
    if (step === 1 && !validateStep1()) return;
    if (step === 2 && !validateStep2()) return;
    setStep(s => s + 1);
  };

  const prevStep = () => {
    setStep(s => s - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const payload = {
        curso_id: formData.curso_id,
        curso_nome: formData.curso_nome,
        projeto_id: formData.vinculo_tipo === 'projeto' ? formData.projeto_id : null,
        projeto_nome: formData.vinculo_tipo === 'projeto' ? formData.projeto_nome : null,
        empresa_id: formData.vinculo_tipo === 'empresa' ? formData.empresa_id : null,
        empresa_nome: formData.vinculo_tipo === 'empresa' ? formData.empresa_nome : null,
        observacoes: formData.observacoes || null,
        alunos: formData.alunos
      };

      await pedidosAPI.criar(payload);
      toast.success('Pedido criado com sucesso!');
      
      // Navigate based on role
      if (user?.role === 'consultor') {
        navigate('/consultor');
      } else if (user?.role === 'assistente') {
        navigate('/assistente');
      } else {
        navigate('/admin/pedidos');
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Erro ao criar pedido');
    } finally {
      setSubmitting(false);
    }
  };

  const getBasePath = () => {
    if (user?.role === 'consultor') return '/consultor';
    if (user?.role === 'assistente') return '/assistente';
    return '/admin';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-[#004587]" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto animate-fadeIn" data-testid="nova-matricula-page">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate(getBasePath())}
          className="mb-4"
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
          Nova Solicitação
        </h1>
        <p className="text-slate-500">
          Preencha os dados para criar uma nova solicitação de matrícula
        </p>
      </div>

      {/* Wizard Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[
            { num: 1, label: 'Dados Básicos', icon: FileText },
            { num: 2, label: 'Alunos', icon: User },
            { num: 3, label: 'Revisão', icon: Check }
          ].map((s, index) => (
            <div key={s.num} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div
                  className={`wizard-step-circle ${
                    step > s.num ? 'completed' : step === s.num ? 'active' : 'pending'
                  }`}
                >
                  {step > s.num ? <Check className="h-4 w-4" /> : <s.icon className="h-4 w-4" />}
                </div>
                <span className="text-xs mt-2 text-slate-600 hidden sm:block">{s.label}</span>
              </div>
              {index < 2 && (
                <div className={`wizard-step-line ${step > s.num ? 'completed' : 'pending'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <Card className="shadow-sm">
        <CardContent className="p-6">
          {/* Step 1: Dados Básicos */}
          {step === 1 && (
            <div className="space-y-6" data-testid="step-1">
              <div className="space-y-2">
                <Label htmlFor="curso">Curso *</Label>
                <Select value={formData.curso_id} onValueChange={handleCursoChange}>
                  <SelectTrigger data-testid="curso-select">
                    <SelectValue placeholder="Selecione o curso" />
                  </SelectTrigger>
                  <SelectContent>
                    {cursos.map((curso) => (
                      <SelectItem key={curso.id} value={curso.id}>
                        {curso.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Vínculo *</Label>
                <RadioGroup
                  value={formData.vinculo_tipo}
                  onValueChange={handleVinculoChange}
                  className="flex gap-4"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="projeto" id="projeto" />
                    <Label htmlFor="projeto" className="cursor-pointer">Projeto</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="empresa" id="empresa" />
                    <Label htmlFor="empresa" className="cursor-pointer">Empresa</Label>
                  </div>
                </RadioGroup>
              </div>

              {formData.vinculo_tipo === 'projeto' && (
                <div className="space-y-2">
                  <Label htmlFor="projeto">Projeto *</Label>
                  <Select value={formData.projeto_id} onValueChange={handleProjetoChange}>
                    <SelectTrigger data-testid="projeto-select">
                      <SelectValue placeholder="Selecione o projeto" />
                    </SelectTrigger>
                    <SelectContent>
                      {projetos.map((projeto) => (
                        <SelectItem key={projeto.id} value={projeto.id}>
                          {projeto.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {formData.vinculo_tipo === 'empresa' && (
                <div className="space-y-2">
                  <Label htmlFor="empresa">Empresa *</Label>
                  <Select value={formData.empresa_id} onValueChange={handleEmpresaChange}>
                    <SelectTrigger data-testid="empresa-select">
                      <SelectValue placeholder="Selecione a empresa" />
                    </SelectTrigger>
                    <SelectContent>
                      {empresas.map((empresa) => (
                        <SelectItem key={empresa.id} value={empresa.id}>
                          {empresa.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="observacoes">Observações</Label>
                <Textarea
                  id="observacoes"
                  value={formData.observacoes}
                  onChange={(e) => setFormData(prev => ({ ...prev, observacoes: e.target.value }))}
                  placeholder="Observações adicionais (opcional)"
                  rows={3}
                  data-testid="observacoes-input"
                />
              </div>
            </div>
          )}

          {/* Step 2: Alunos */}
          {step === 2 && (
            <div className="space-y-6" data-testid="step-2">
              {formData.alunos.map((aluno, index) => (
                <Card key={index} className="border-slate-200">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">
                        Aluno {index + 1}
                      </CardTitle>
                      {formData.alunos.length > 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeAluno(index)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          data-testid={`remove-aluno-${index}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Dados Pessoais */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="md:col-span-2">
                        <Label>Nome Completo *</Label>
                        <Input
                          value={aluno.nome}
                          onChange={(e) => handleAlunoChange(index, 'nome', e.target.value)}
                          onBlur={() => handleNomeBlur(index)}
                          placeholder="Nome completo do aluno"
                          data-testid={`aluno-${index}-nome`}
                        />
                        <p className="text-xs text-slate-500 mt-1">O nome será formatado automaticamente (ex: "Pedro Henrique da Silva")</p>
                      </div>
                      <div>
                        <Label>CPF *</Label>
                        <Input
                          value={aluno.cpf}
                          onChange={(e) => handleAlunoChange(index, 'cpf', e.target.value)}
                          placeholder="000.000.000-00"
                          data-testid={`aluno-${index}-cpf`}
                        />
                      </div>
                      <div>
                        <Label>Data de Nascimento *</Label>
                        <Input
                          type="date"
                          value={aluno.data_nascimento}
                          onChange={(e) => handleAlunoChange(index, 'data_nascimento', e.target.value)}
                          data-testid={`aluno-${index}-nascimento`}
                        />
                      </div>
                      <div>
                        <Label>Email *</Label>
                        <Input
                          type="email"
                          value={aluno.email}
                          onChange={(e) => handleAlunoChange(index, 'email', e.target.value)}
                          placeholder="email@exemplo.com"
                          data-testid={`aluno-${index}-email`}
                        />
                      </div>
                      <div>
                        <Label>Telefone *</Label>
                        <Input
                          value={aluno.telefone}
                          onChange={(e) => handleAlunoChange(index, 'telefone', e.target.value)}
                          placeholder="(00) 00000-0000"
                          data-testid={`aluno-${index}-telefone`}
                        />
                      </div>
                    </div>

                    {/* Documento */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div>
                        <Label>RG *</Label>
                        <Input
                          value={aluno.rg}
                          onChange={(e) => handleAlunoChange(index, 'rg', e.target.value)}
                          placeholder="00000000"
                          data-testid={`aluno-${index}-rg`}
                        />
                      </div>
                      <div>
                        <Label>Órgão Emissor *</Label>
                        <Input
                          value={aluno.rg_orgao_emissor}
                          onChange={(e) => handleAlunoChange(index, 'rg_orgao_emissor', e.target.value)}
                          placeholder="SSP"
                          data-testid={`aluno-${index}-orgao`}
                        />
                      </div>
                      <div>
                        <Label>UF do RG *</Label>
                        <Select
                          value={aluno.rg_uf}
                          onValueChange={(v) => handleAlunoChange(index, 'rg_uf', v)}
                        >
                          <SelectTrigger data-testid={`aluno-${index}-rg-uf`}>
                            <SelectValue placeholder="UF" />
                          </SelectTrigger>
                          <SelectContent>
                            {ESTADOS_BR.map((uf) => (
                              <SelectItem key={uf} value={uf}>{uf}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Data de Emissão RG *</Label>
                        <Input
                          type="date"
                          value={aluno.rg_data_emissao}
                          onChange={(e) => handleAlunoChange(index, 'rg_data_emissao', e.target.value)}
                          data-testid={`aluno-${index}-rg-emissao`}
                        />
                      </div>
                    </div>

                    {/* Dados Complementares TOTVS */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <Label>Naturalidade (Cidade) *</Label>
                        <Input
                          value={aluno.naturalidade}
                          onChange={(e) => handleAlunoChange(index, 'naturalidade', e.target.value)}
                          onBlur={() => handleEnderecoBlur(index, 'naturalidade')}
                          placeholder="Cidade de nascimento"
                          data-testid={`aluno-${index}-naturalidade`}
                        />
                      </div>
                      <div>
                        <Label>Naturalidade (UF) *</Label>
                        <Select
                          value={aluno.naturalidade_uf}
                          onValueChange={(v) => handleAlunoChange(index, 'naturalidade_uf', v)}
                        >
                          <SelectTrigger data-testid={`aluno-${index}-naturalidade-uf`}>
                            <SelectValue placeholder="UF de nascimento" />
                          </SelectTrigger>
                          <SelectContent>
                            {ESTADOS_BR.map((uf) => (
                              <SelectItem key={uf} value={uf}>{uf}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Sexo *</Label>
                        <Select
                          value={aluno.sexo}
                          onValueChange={(v) => handleAlunoChange(index, 'sexo', v)}
                        >
                          <SelectTrigger data-testid={`aluno-${index}-sexo`}>
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="M">Masculino</SelectItem>
                            <SelectItem value="F">Feminino</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label>Cor/Raça *</Label>
                        <Select
                          value={aluno.cor_raca}
                          onValueChange={(v) => handleAlunoChange(index, 'cor_raca', v)}
                        >
                          <SelectTrigger data-testid={`aluno-${index}-cor-raca`}>
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                          <SelectContent>
                            {COR_RACA_OPTIONS.map((opcao) => (
                              <SelectItem key={opcao} value={opcao}>{opcao}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Grau de Instrução *</Label>
                        <Select
                          value={aluno.grau_instrucao}
                          onValueChange={(v) => handleAlunoChange(index, 'grau_instrucao', v)}
                        >
                          <SelectTrigger data-testid={`aluno-${index}-grau-instrucao`}>
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                          <SelectContent>
                            {GRAU_INSTRUCAO_OPTIONS.map((opcao) => (
                              <SelectItem key={opcao} value={opcao}>{opcao}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Filiação */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label>Nome do Pai *</Label>
                        <Input
                          value={aluno.nome_pai}
                          onChange={(e) => handleAlunoChange(index, 'nome_pai', e.target.value)}
                          onBlur={() => {
                            setFormData(prev => {
                              const alunos = [...prev.alunos];
                              alunos[index] = { ...alunos[index], nome_pai: formatarNomeProprio(alunos[index].nome_pai) };
                              return { ...prev, alunos };
                            });
                          }}
                          placeholder="Nome completo do pai"
                          data-testid={`aluno-${index}-nome-pai`}
                        />
                      </div>
                      <div>
                        <Label>Nome da Mãe *</Label>
                        <Input
                          value={aluno.nome_mae}
                          onChange={(e) => handleAlunoChange(index, 'nome_mae', e.target.value)}
                          onBlur={() => {
                            setFormData(prev => {
                              const alunos = [...prev.alunos];
                              alunos[index] = { ...alunos[index], nome_mae: formatarNomeProprio(alunos[index].nome_mae) };
                              return { ...prev, alunos };
                            });
                          }}
                          placeholder="Nome completo da mãe"
                          data-testid={`aluno-${index}-nome-mae`}
                        />
                      </div>
                    </div>

                    {/* Endereço */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <Label>CEP *</Label>
                        <div className="relative">
                          <Input
                            value={aluno.endereco_cep}
                            onChange={(e) => handleAlunoChange(index, 'endereco_cep', e.target.value)}
                            onBlur={(e) => buscarCep(index, e.target.value)}
                            placeholder="00000-000"
                            data-testid={`aluno-${index}-cep`}
                            className={buscandoCep[index] ? 'pr-10' : ''}
                          />
                          {buscandoCep[index] && (
                            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-blue-500" />
                          )}
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <Label>Logradouro *</Label>
                        <Input
                          value={aluno.endereco_logradouro}
                          onChange={(e) => handleAlunoChange(index, 'endereco_logradouro', e.target.value)}
                          onBlur={() => handleEnderecoBlur(index, 'endereco_logradouro')}
                          placeholder="Rua, Avenida..."
                          data-testid={`aluno-${index}-logradouro`}
                        />
                      </div>
                      <div>
                        <Label>Número *</Label>
                        <Input
                          value={aluno.endereco_numero}
                          onChange={(e) => handleAlunoChange(index, 'endereco_numero', e.target.value)}
                          placeholder="123"
                          data-testid={`aluno-${index}-numero`}
                        />
                      </div>
                      <div>
                        <Label>Complemento</Label>
                        <Input
                          value={aluno.endereco_complemento}
                          onChange={(e) => handleAlunoChange(index, 'endereco_complemento', e.target.value)}
                          placeholder="Apto, Bloco..."
                          data-testid={`aluno-${index}-complemento`}
                        />
                      </div>
                      <div>
                        <Label>Bairro *</Label>
                        <Input
                          value={aluno.endereco_bairro}
                          onChange={(e) => handleAlunoChange(index, 'endereco_bairro', e.target.value)}
                          onBlur={() => handleEnderecoBlur(index, 'endereco_bairro')}
                          placeholder="Bairro"
                          data-testid={`aluno-${index}-bairro`}
                        />
                      </div>
                      <div>
                        <Label>Cidade *</Label>
                        <Input
                          value={aluno.endereco_cidade}
                          onChange={(e) => handleAlunoChange(index, 'endereco_cidade', e.target.value)}
                          onBlur={() => handleEnderecoBlur(index, 'endereco_cidade')}
                          placeholder="Cidade"
                          data-testid={`aluno-${index}-cidade`}
                        />
                      </div>
                      <div>
                        <Label>UF *</Label>
                        <Select
                          value={aluno.endereco_uf}
                          onValueChange={(v) => handleAlunoChange(index, 'endereco_uf', v)}
                        >
                          <SelectTrigger data-testid={`aluno-${index}-endereco-uf`}>
                            <SelectValue placeholder="UF" />
                          </SelectTrigger>
                          <SelectContent>
                            {ESTADOS_BR.map((uf) => (
                              <SelectItem key={uf} value={uf}>{uf}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              <Button
                variant="outline"
                onClick={addAluno}
                className="w-full"
                data-testid="add-aluno-btn"
              >
                <Plus className="h-4 w-4 mr-2" />
                Adicionar Aluno
              </Button>
            </div>
          )}

          {/* Step 3: Revisão */}
          {step === 3 && (
            <div className="space-y-6" data-testid="step-3">
              <Card className="bg-slate-50 border-slate-200">
                <CardHeader>
                  <CardTitle className="text-base">Dados do Pedido</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p><strong>Curso:</strong> {formData.curso_nome}</p>
                  {formData.projeto_nome && (
                    <p><strong>Projeto:</strong> {formData.projeto_nome}</p>
                  )}
                  {formData.empresa_nome && (
                    <p><strong>Empresa:</strong> {formData.empresa_nome}</p>
                  )}
                  {formData.observacoes && (
                    <p><strong>Observações:</strong> {formData.observacoes}</p>
                  )}
                </CardContent>
              </Card>

              <Card className="bg-slate-50 border-slate-200">
                <CardHeader>
                  <CardTitle className="text-base">Alunos ({formData.alunos.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {formData.alunos.map((aluno, index) => (
                      <div key={index} className="p-4 bg-white rounded-lg border border-slate-200">
                        <p className="font-semibold">{aluno.nome}</p>
                        <p className="text-sm text-slate-600">CPF: {aluno.cpf}</p>
                        <p className="text-sm text-slate-600">Email: {aluno.email}</p>
                        <p className="text-sm text-slate-600">Telefone: {aluno.telefone}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t">
            {step > 1 ? (
              <Button variant="outline" onClick={prevStep} data-testid="prev-btn">
                <ChevronLeft className="h-4 w-4 mr-2" />
                Anterior
              </Button>
            ) : (
              <div />
            )}

            {step < 3 ? (
              <Button onClick={nextStep} className="bg-[#004587] hover:bg-[#003366]" data-testid="next-btn">
                Próximo
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={submitting}
                className="bg-[#E30613] hover:bg-[#b9050f]"
                data-testid="submit-btn"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Enviar Solicitação
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default NovaMatriculaPage;
