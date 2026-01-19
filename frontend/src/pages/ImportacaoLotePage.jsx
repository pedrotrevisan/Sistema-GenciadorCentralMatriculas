import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { auxiliaresAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';
import { 
  ChevronLeft, 
  Upload, 
  FileSpreadsheet, 
  Download,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  Sparkles,
  Zap,
  Users
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ImportacaoLotePage = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  // Estados
  const [step, setStep] = useState(1); // 1: Config, 2: Upload, 3: Preview, 4: Resultado
  const [loading, setLoading] = useState(false);
  const [validando, setValidando] = useState(false);
  const [importando, setImportando] = useState(false);
  
  // Dados auxiliares
  const [cursos, setCursos] = useState([]);
  const [projetos, setProjetos] = useState([]);
  const [empresas, setEmpresas] = useState([]);
  
  // Configurações
  const [cursoId, setCursoId] = useState('');
  const [cursoNome, setCursoNome] = useState('');
  const [vinculoTipo, setVinculoTipo] = useState('projeto');
  const [projetoId, setProjetoId] = useState('');
  const [projetoNome, setProjetoNome] = useState('');
  const [empresaId, setEmpresaId] = useState('');
  const [empresaNome, setEmpresaNome] = useState('');
  
  // Arquivo e validação
  const [arquivo, setArquivo] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [validacaoResult, setValidacaoResult] = useState(null);
  const [importacaoResult, setImportacaoResult] = useState(null);
  
  // Animação de parsing
  const [parsing, setParsing] = useState(false);

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

  const handleCursoChange = (id) => {
    const curso = cursos.find(c => c.id === id);
    setCursoId(id);
    setCursoNome(curso?.nome || '');
  };

  const handleProjetoChange = (id) => {
    const projeto = projetos.find(p => p.id === id);
    setProjetoId(id);
    setProjetoNome(projeto?.nome || '');
  };

  const handleEmpresaChange = (id) => {
    const empresa = empresas.find(e => e.id === id);
    setEmpresaId(id);
    setEmpresaNome(empresa?.nome || '');
  };

  // Drag and Drop handlers
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv')) {
        setArquivo(file);
        validarArquivo(file);
      } else {
        toast.error('Formato inválido. Use .xlsx, .xls ou .csv');
      }
    }
  }, []);

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setArquivo(file);
      validarArquivo(file);
    }
  };

  const validarArquivo = async (file) => {
    setValidando(true);
    setParsing(true);
    
    // Simular animação de parsing
    await new Promise(resolve => setTimeout(resolve, 1500));
    setParsing(false);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const params = new URLSearchParams();
      params.append('curso_id', cursoId);
      if (vinculoTipo === 'projeto' && projetoId) {
        params.append('projeto_id', projetoId);
      }
      if (vinculoTipo === 'empresa' && empresaId) {
        params.append('empresa_id', empresaId);
      }
      
      const response = await axios.post(
        `${API_URL}/api/importacao/validar?${params.toString()}`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      setValidacaoResult(response.data);
      setStep(3);
      
      if (response.data.sucesso) {
        toast.success(`${response.data.linhas_validas} alunos prontos para importar!`);
      } else {
        toast.warning(`${response.data.linhas_com_erro} linhas com erro encontradas`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao validar arquivo');
    } finally {
      setValidando(false);
    }
  };

  const executarImportacao = async () => {
    setImportando(true);
    
    try {
      const formData = new FormData();
      formData.append('file', arquivo);
      
      const params = new URLSearchParams();
      params.append('curso_id', cursoId);
      params.append('curso_nome', cursoNome);
      if (vinculoTipo === 'projeto' && projetoId) {
        params.append('projeto_id', projetoId);
        params.append('projeto_nome', projetoNome);
      }
      if (vinculoTipo === 'empresa' && empresaId) {
        params.append('empresa_id', empresaId);
        params.append('empresa_nome', empresaNome);
      }
      
      const response = await axios.post(
        `${API_URL}/api/importacao/executar?${params.toString()}`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      setImportacaoResult(response.data);
      setStep(4);
      
      if (response.data.pedidos_criados > 0) {
        toast.success(`${response.data.pedidos_criados} matrículas criadas com sucesso!`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao executar importação');
    } finally {
      setImportando(false);
    }
  };

  const downloadTemplate = () => {
    window.open(`${API_URL}/api/importacao/template`, '_blank');
  };

  const resetar = () => {
    setStep(1);
    setArquivo(null);
    setValidacaoResult(null);
    setImportacaoResult(null);
  };

  const getBasePath = () => {
    if (user?.role === 'consultor') return '/consultor';
    if (user?.role === 'assistente') return '/assistente';
    return '/admin';
  };

  const canProceedStep1 = cursoId && ((vinculoTipo === 'projeto' && projetoId) || (vinculoTipo === 'empresa' && empresaId));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-[#004587]" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto animate-fadeIn" data-testid="importacao-lote-page">
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
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-br from-[#004587] to-[#0066cc] rounded-xl">
            <Users className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 font-['Chivo']">
              Importação em Lote
            </h1>
            <p className="text-slate-500">
              Importe múltiplos alunos de uma só vez via planilha Excel/CSV
            </p>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[
            { num: 1, label: 'Configurar' },
            { num: 2, label: 'Upload' },
            { num: 3, label: 'Validar' },
            { num: 4, label: 'Resultado' }
          ].map((s, index) => (
            <div key={s.num} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                    step > s.num 
                      ? 'bg-green-500 text-white' 
                      : step === s.num 
                        ? 'bg-[#004587] text-white ring-4 ring-[#004587]/20' 
                        : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {step > s.num ? <CheckCircle className="h-5 w-5" /> : s.num}
                </div>
                <span className="text-xs mt-2 text-slate-600 hidden sm:block">{s.label}</span>
              </div>
              {index < 3 && (
                <div className={`flex-1 h-1 mx-2 rounded ${step > s.num ? 'bg-green-500' : 'bg-slate-200'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step 1: Configuração */}
      {step === 1 && (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[#004587]" />
              Configuração da Importação
            </CardTitle>
            <CardDescription>
              Selecione o curso e o vínculo (projeto ou empresa) para os alunos
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Curso *</Label>
              <Select value={cursoId} onValueChange={handleCursoChange}>
                <SelectTrigger data-testid="curso-select">
                  <SelectValue placeholder="Selecione o curso" />
                </SelectTrigger>
                <SelectContent>
                  {cursos.filter(c => c.ativo !== false).map((curso) => (
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
                value={vinculoTipo}
                onValueChange={(v) => {
                  setVinculoTipo(v);
                  setProjetoId('');
                  setProjetoNome('');
                  setEmpresaId('');
                  setEmpresaNome('');
                }}
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

            {vinculoTipo === 'projeto' && (
              <div className="space-y-2">
                <Label>Projeto *</Label>
                <Select value={projetoId} onValueChange={handleProjetoChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o projeto" />
                  </SelectTrigger>
                  <SelectContent>
                    {projetos.filter(p => p.ativo !== false).map((projeto) => (
                      <SelectItem key={projeto.id} value={projeto.id}>
                        {projeto.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {vinculoTipo === 'empresa' && (
              <div className="space-y-2">
                <Label>Empresa *</Label>
                <Select value={empresaId} onValueChange={handleEmpresaChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione a empresa" />
                  </SelectTrigger>
                  <SelectContent>
                    {empresas.filter(e => e.ativo !== false).map((empresa) => (
                      <SelectItem key={empresa.id} value={empresa.id}>
                        {empresa.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="flex justify-between pt-4 border-t">
              <Button variant="outline" onClick={downloadTemplate}>
                <Download className="h-4 w-4 mr-2" />
                Baixar Template
              </Button>
              <Button 
                onClick={() => setStep(2)} 
                disabled={!canProceedStep1}
                className="bg-[#004587] hover:bg-[#003366]"
              >
                Continuar
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Upload */}
      {step === 2 && (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-[#004587]" />
              Upload da Planilha
            </CardTitle>
            <CardDescription>
              Arraste sua planilha ou clique para selecionar
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Drop Zone */}
            <div
              className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
                dragActive 
                  ? 'border-[#004587] bg-[#004587]/5 scale-[1.02]' 
                  : validando || parsing
                    ? 'border-[#004587] bg-[#004587]/5'
                    : 'border-slate-300 hover:border-[#004587] hover:bg-slate-50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {parsing ? (
                <div className="space-y-4">
                  <div className="relative">
                    <div className="w-20 h-20 mx-auto rounded-full bg-[#004587]/10 flex items-center justify-center">
                      <Zap className="h-10 w-10 text-[#004587] animate-pulse" />
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-24 h-24 border-4 border-[#004587]/30 border-t-[#004587] rounded-full animate-spin" />
                    </div>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-[#004587]">Processando dados...</p>
                    <p className="text-sm text-slate-500 mt-1">Validando cada linha da planilha</p>
                  </div>
                  {/* Animação de código estilo Matrix */}
                  <div className="font-mono text-xs text-[#004587]/60 space-y-1 max-h-20 overflow-hidden">
                    <p className="animate-pulse">{'> Lendo arquivo...'}</p>
                    <p className="animate-pulse delay-100">{'> Validando CPFs...'}</p>
                    <p className="animate-pulse delay-200">{'> Verificando duplicidades...'}</p>
                    <p className="animate-pulse delay-300">{'> Formatando nomes...'}</p>
                  </div>
                </div>
              ) : validando ? (
                <div className="space-y-4">
                  <Loader2 className="h-12 w-12 mx-auto text-[#004587] animate-spin" />
                  <p className="text-slate-600">Enviando para validação...</p>
                </div>
              ) : (
                <>
                  <input
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    onChange={handleFileSelect}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    data-testid="file-input"
                  />
                  <div className="space-y-4">
                    <div className={`w-20 h-20 mx-auto rounded-full flex items-center justify-center transition-all ${
                      dragActive ? 'bg-[#004587] scale-110' : 'bg-slate-100'
                    }`}>
                      <FileSpreadsheet className={`h-10 w-10 transition-colors ${
                        dragActive ? 'text-white' : 'text-slate-400'
                      }`} />
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-slate-700">
                        {dragActive ? 'Solte o arquivo aqui!' : 'Arraste sua planilha aqui'}
                      </p>
                      <p className="text-sm text-slate-500 mt-1">
                        ou clique para selecionar • .xlsx, .xls ou .csv
                      </p>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Info do arquivo selecionado */}
            {arquivo && !validando && !parsing && (
              <div className="mt-4 p-4 bg-slate-50 rounded-lg flex items-center gap-3">
                <FileSpreadsheet className="h-8 w-8 text-green-600" />
                <div className="flex-1">
                  <p className="font-medium text-slate-900">{arquivo.name}</p>
                  <p className="text-sm text-slate-500">
                    {(arquivo.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setArquivo(null)}>
                  Remover
                </Button>
              </div>
            )}

            <div className="flex justify-between pt-6 border-t mt-6">
              <Button variant="outline" onClick={() => setStep(1)}>
                <ChevronLeft className="h-4 w-4 mr-2" />
                Voltar
              </Button>
              <Button variant="outline" onClick={downloadTemplate}>
                <Download className="h-4 w-4 mr-2" />
                Baixar Template
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Preview/Validação */}
      {step === 3 && validacaoResult && (
        <div className="space-y-6">
          {/* Resumo */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-slate-50">
              <CardContent className="p-4">
                <p className="text-sm text-slate-600">Total de Linhas</p>
                <p className="text-2xl font-bold text-slate-900">{validacaoResult.total_linhas}</p>
              </CardContent>
            </Card>
            <Card className="bg-green-50">
              <CardContent className="p-4">
                <p className="text-sm text-green-600">Válidas</p>
                <p className="text-2xl font-bold text-green-700">{validacaoResult.linhas_validas}</p>
              </CardContent>
            </Card>
            <Card className="bg-red-50">
              <CardContent className="p-4">
                <p className="text-sm text-red-600">Com Erros</p>
                <p className="text-2xl font-bold text-red-700">{validacaoResult.linhas_com_erro}</p>
              </CardContent>
            </Card>
            <Card className={validacaoResult.sucesso ? 'bg-green-50' : 'bg-yellow-50'}>
              <CardContent className="p-4">
                <p className="text-sm text-slate-600">Status</p>
                <div className="flex items-center gap-2">
                  {validacaoResult.sucesso ? (
                    <>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span className="font-semibold text-green-700">Pronto!</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      <span className="font-semibold text-yellow-700">Revisar</span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabela de Preview */}
          <Card>
            <CardHeader>
              <CardTitle>Preview dos Dados</CardTitle>
              <CardDescription>
                Verifique os dados antes de confirmar a importação
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                <Table>
                  <TableHeader className="sticky top-0 bg-white">
                    <TableRow>
                      <TableHead className="w-16">Linha</TableHead>
                      <TableHead>Nome</TableHead>
                      <TableHead>CPF</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {validacaoResult.preview.map((item) => (
                      <TableRow 
                        key={item.linha}
                        className={!item.valido ? 'bg-red-50' : ''}
                      >
                        <TableCell className="font-mono">{item.linha}</TableCell>
                        <TableCell className="font-medium">{item.nome}</TableCell>
                        <TableCell className="font-mono text-sm">{item.cpf}</TableCell>
                        <TableCell className="text-sm">{item.email}</TableCell>
                        <TableCell>
                          {item.valido ? (
                            <Badge className="bg-green-100 text-green-800">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              OK
                            </Badge>
                          ) : (
                            <div className="space-y-1">
                              <Badge variant="destructive">
                                <XCircle className="h-3 w-3 mr-1" />
                                Erro
                              </Badge>
                              <div className="text-xs text-red-600">
                                {item.erros.join(', ')}
                              </div>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Ações */}
          <div className="flex justify-between">
            <Button variant="outline" onClick={resetar}>
              <ChevronLeft className="h-4 w-4 mr-2" />
              Recomeçar
            </Button>
            <div className="flex gap-3">
              {validacaoResult.linhas_com_erro > 0 && (
                <p className="text-sm text-yellow-600 self-center">
                  ⚠️ Linhas com erro serão ignoradas
                </p>
              )}
              <Button
                onClick={executarImportacao}
                disabled={importando || validacaoResult.linhas_validas === 0}
                className="bg-[#E30613] hover:bg-[#b9050f]"
              >
                {importando ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Importando...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Importar {validacaoResult.linhas_validas} Alunos
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Step 4: Resultado */}
      {step === 4 && importacaoResult && (
        <Card className="shadow-lg">
          <CardContent className="p-12 text-center">
            {importacaoResult.pedidos_criados > 0 ? (
              <>
                <div className="w-20 h-20 mx-auto rounded-full bg-green-100 flex items-center justify-center mb-6">
                  <CheckCircle className="h-10 w-10 text-green-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">
                  Importação Concluída!
                </h2>
                <p className="text-slate-600 mb-6">
                  {importacaoResult.pedidos_criados} matrículas foram criadas com sucesso
                </p>
                
                {importacaoResult.erros.length > 0 && (
                  <div className="mb-6 p-4 bg-yellow-50 rounded-lg text-left max-w-md mx-auto">
                    <p className="font-semibold text-yellow-800 mb-2">
                      {importacaoResult.erros.length} linhas não foram importadas:
                    </p>
                    <ul className="text-sm text-yellow-700 space-y-1 max-h-32 overflow-auto">
                      {importacaoResult.erros.slice(0, 5).map((e, i) => (
                        <li key={i}>Linha {e.linha}: {e.erro}</li>
                      ))}
                      {importacaoResult.erros.length > 5 && (
                        <li>... e mais {importacaoResult.erros.length - 5} erros</li>
                      )}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="w-20 h-20 mx-auto rounded-full bg-red-100 flex items-center justify-center mb-6">
                  <XCircle className="h-10 w-10 text-red-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">
                  Nenhuma matrícula criada
                </h2>
                <p className="text-slate-600 mb-6">
                  Todas as linhas apresentaram erros
                </p>
              </>
            )}
            
            <div className="flex justify-center gap-4">
              <Button variant="outline" onClick={resetar}>
                Nova Importação
              </Button>
              <Button 
                onClick={() => navigate(getBasePath() === '/admin' ? '/admin/pedidos' : getBasePath())}
                className="bg-[#004587] hover:bg-[#003366]"
              >
                Ver Pedidos
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ImportacaoLotePage;
