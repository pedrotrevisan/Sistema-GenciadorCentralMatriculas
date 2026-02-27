import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { toast } from 'sonner';
import api from '../services/api';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  RefreshCw,
  Copy,
  Check,
  User,
  Phone,
  Mail,
  FileText,
  Building,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { cn } from '../lib/utils';

const FormatadorPlanilhaPage = () => {
  const [arquivo, setArquivo] = useState(null);
  const [processando, setProcessando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [alunoExpandido, setAlunoExpandido] = useState(null);
  const [copiado, setCopiado] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Validar arquivo
  const validarArquivo = (file) => {
    if (!file) return false;
    const nome = file.name.toLowerCase();
    if (!nome.endsWith('.xls') && !nome.endsWith('.xlsx')) {
      toast.error('Arquivo deve ser Excel (.xls ou .xlsx)');
      return false;
    }
    return true;
  };

  // Handler para seleção via input
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && validarArquivo(file)) {
      setArquivo(file);
      setResultado(null);
      toast.success(`Arquivo "${file.name}" selecionado!`);
    }
  };

  // Handlers para Drag & Drop
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (validarArquivo(file)) {
        setArquivo(file);
        setResultado(null);
        toast.success(`Arquivo "${file.name}" selecionado!`);
      }
    }
  };

  const processarPlanilha = async () => {
    if (!arquivo) {
      toast.error('Selecione um arquivo primeiro');
      return;
    }

    setProcessando(true);
    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);

      const response = await api.post('/formatador/processar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setResultado(response.data);
      toast.success(`Planilha processada! ${response.data.total} alunos encontrados.`);
    } catch (error) {
      console.error('Erro ao processar:', error);
      toast.error('Erro ao processar planilha');
    } finally {
      setProcessando(false);
    }
  };

  const baixarFormatado = async () => {
    if (!arquivo) return;

    setProcessando(true);
    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);

      const response = await api.post('/formatador/processar-e-baixar', formData, {
        responseType: 'blob',
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Criar blob com tipo MIME correto para Excel
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      
      // Gerar nome do arquivo
      const nomeOriginal = arquivo.name.toLowerCase();
      const nomeFormatado = nomeOriginal.endsWith('.xlsx') 
        ? arquivo.name.replace('.xlsx', '_FORMATADO.xlsx')
        : arquivo.name.replace('.xls', '_FORMATADO.xlsx');
      
      // Download do arquivo
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = nomeFormatado; // Usar .download ao invés de setAttribute
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);

      toast.success('Planilha formatada baixada!');
    } catch (error) {
      console.error('Erro ao baixar:', error);
      toast.error('Erro ao gerar planilha formatada');
    } finally {
      setProcessando(false);
    }
  };

  const copiarDados = async (aluno, tipo) => {
    const fmt = aluno.formatado;
    let texto = '';

    if (tipo === 'completo') {
      texto = `Nome: ${fmt.nome}
CPF: ${fmt.cpf}
Email: ${fmt.email}
Telefone: ${fmt.telefone}
RG: ${fmt.rg} - ${fmt.orgao_emissor}
Data Nascimento: ${fmt.data_nascimento}
Endereço: ${fmt.endereco}, ${fmt.numero} - ${fmt.bairro} - CEP ${fmt.cep}`;
    } else if (tipo === 'erro') {
      texto = `CPF INVÁLIDO - ${fmt.nome}

O CPF informado (${fmt.cpf}) está inválido no validador.
Por favor, confirme o CPF correto (11 dígitos) para prosseguir com a matrícula.

Erros encontrados:
${aluno.erros.map(e => `• ${e}`).join('\n')}`;
    }

    try {
      await navigator.clipboard.writeText(texto);
      setCopiado(`${aluno.linha}-${tipo}`);
      toast.success('Copiado!');
      setTimeout(() => setCopiado(null), 2000);
    } catch (err) {
      toast.error('Erro ao copiar');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'OK':
        return <Badge className="bg-green-500"><CheckCircle2 className="w-3 h-3 mr-1" />OK</Badge>;
      case 'ERRO':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Erro</Badge>;
      case 'AVISO':
        return <Badge className="bg-amber-500"><AlertTriangle className="w-3 h-3 mr-1" />Aviso</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6" data-testid="formatador-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Formatador de Planilhas</h1>
        <p className="text-slate-500">
          Processa e valida planilhas de matrícula automaticamente
        </p>
      </div>

      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-green-600" />
            Upload de Planilha
          </CardTitle>
          <CardDescription>
            Selecione a planilha Excel (.xls ou .xlsx) enviada pela empresa
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div 
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200",
              arquivo ? "border-green-300 bg-green-50" : "border-slate-300 hover:border-slate-400",
              isDragging && "border-blue-500 bg-blue-50 scale-[1.02]"
            )}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept=".xls,.xlsx"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
              data-testid="file-input"
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              {isDragging ? (
                <div className="space-y-2">
                  <Upload className="w-12 h-12 mx-auto text-blue-500 animate-bounce" />
                  <p className="font-medium text-blue-600">
                    Solte o arquivo aqui!
                  </p>
                </div>
              ) : arquivo ? (
                <div className="space-y-2">
                  <FileSpreadsheet className="w-12 h-12 mx-auto text-green-600" />
                  <p className="font-medium text-green-700">{arquivo.name}</p>
                  <p className="text-sm text-green-600">
                    {(arquivo.size / 1024).toFixed(1)} KB
                  </p>
                  <Button variant="outline" size="sm" className="mt-2" type="button">
                    Trocar arquivo
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="w-12 h-12 mx-auto text-slate-400" />
                  <p className="font-medium text-slate-600">
                    Clique para selecionar ou arraste o arquivo
                  </p>
                  <p className="text-sm text-slate-400">
                    Suporta .xls e .xlsx
                  </p>
                </div>
              )}
            </label>
          </div>

          {arquivo && (
            <div className="flex gap-3">
              <Button 
                onClick={processarPlanilha} 
                disabled={processando}
                className="flex-1"
                data-testid="processar-btn"
              >
                {processando ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                )}
                Processar e Validar
              </Button>
              <Button 
                onClick={baixarFormatado} 
                disabled={processando}
                variant="outline"
                data-testid="baixar-btn"
              >
                <Download className="w-4 h-4 mr-2" />
                Baixar Formatado
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resultado */}
      {resultado && (
        <>
          {/* Resumo */}
          <Card>
            <CardHeader>
              <CardTitle>Resultado do Processamento</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {resultado.empresa?.nome && (
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-2 text-blue-700">
                      <Building className="w-5 h-5" />
                      <span className="font-medium">Empresa</span>
                    </div>
                    <p className="mt-1 text-blue-800 font-semibold">
                      {resultado.empresa.nome}
                    </p>
                  </div>
                )}
                <div className="p-4 bg-slate-100 rounded-lg text-center">
                  <p className="text-3xl font-bold text-slate-800">{resultado.total}</p>
                  <p className="text-sm text-slate-500">Total de Alunos</p>
                </div>
                <div className="p-4 bg-green-100 rounded-lg text-center">
                  <p className="text-3xl font-bold text-green-700">{resultado.resumo.ok}</p>
                  <p className="text-sm text-green-600">OK</p>
                </div>
                <div className="p-4 bg-red-100 rounded-lg text-center">
                  <p className="text-3xl font-bold text-red-700">{resultado.resumo.erro}</p>
                  <p className="text-sm text-red-600">Com Erro</p>
                </div>
              </div>

              {resultado.resumo.erro > 0 && (
                <Alert className="mt-4 bg-red-50 border-red-200">
                  <XCircle className="w-4 h-4 text-red-600" />
                  <AlertDescription className="text-red-700">
                    <strong>{resultado.resumo.erro} aluno(s)</strong> com dados inválidos. 
                    Verifique os CPFs marcados em vermelho abaixo.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Lista de Alunos */}
          <Card>
            <CardHeader>
              <CardTitle>Alunos Processados</CardTitle>
              <CardDescription>
                Clique em um aluno para ver detalhes e copiar dados
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {resultado.alunos.map((aluno, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      "border rounded-lg overflow-hidden transition-all",
                      aluno.status === 'ERRO' ? "border-red-300 bg-red-50" :
                      aluno.status === 'AVISO' ? "border-amber-300 bg-amber-50" :
                      "border-slate-200 hover:border-slate-300"
                    )}
                  >
                    {/* Header do aluno */}
                    <div 
                      className="p-4 flex items-center justify-between cursor-pointer"
                      onClick={() => setAlunoExpandido(alunoExpandido === idx ? null : idx)}
                      data-testid={`aluno-${idx}`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-sm font-medium">
                          {aluno.linha - 11}
                        </div>
                        <div>
                          <p className="font-medium text-slate-800">
                            {aluno.formatado.nome}
                          </p>
                          <div className="flex items-center gap-3 text-sm text-slate-500">
                            <span className="flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              {aluno.formatado.cpf}
                            </span>
                            <span className="flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              {aluno.formatado.telefone}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {getStatusBadge(aluno.status)}
                        {alunoExpandido === idx ? (
                          <ChevronUp className="w-5 h-5 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {/* Detalhes expandidos */}
                    {alunoExpandido === idx && (
                      <div className="px-4 pb-4 border-t border-slate-200 pt-4">
                        {/* Erros */}
                        {aluno.erros.length > 0 && (
                          <Alert className="mb-4 bg-red-100 border-red-300">
                            <XCircle className="w-4 h-4 text-red-600" />
                            <AlertDescription>
                              <ul className="list-disc ml-4 text-red-700">
                                {aluno.erros.map((erro, i) => (
                                  <li key={i}>{erro}</li>
                                ))}
                              </ul>
                            </AlertDescription>
                          </Alert>
                        )}

                        {/* Comparativo */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-medium text-slate-700 mb-2">Original</h4>
                            <div className="space-y-1 text-sm">
                              <p><span className="text-slate-500">Nome:</span> {aluno.original.nome}</p>
                              <p><span className="text-slate-500">CPF:</span> {aluno.original.cpf}</p>
                              <p><span className="text-slate-500">Tel:</span> {aluno.original.telefone}</p>
                              <p><span className="text-slate-500">Email:</span> {aluno.original.email}</p>
                            </div>
                          </div>
                          <div>
                            <h4 className="font-medium text-green-700 mb-2">Formatado</h4>
                            <div className="space-y-1 text-sm">
                              <p><span className="text-slate-500">Nome:</span> <strong>{aluno.formatado.nome}</strong></p>
                              <p><span className="text-slate-500">CPF:</span> <strong>{aluno.formatado.cpf}</strong></p>
                              <p><span className="text-slate-500">Tel:</span> <strong>{aluno.formatado.telefone}</strong></p>
                              <p><span className="text-slate-500">Email:</span> <strong>{aluno.formatado.email}</strong></p>
                            </div>
                          </div>
                        </div>

                        {/* Botões de ação */}
                        <div className="flex gap-2 mt-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copiarDados(aluno, 'completo')}
                          >
                            {copiado === `${aluno.linha}-completo` ? (
                              <Check className="w-3 h-3 mr-1" />
                            ) : (
                              <Copy className="w-3 h-3 mr-1" />
                            )}
                            Copiar Dados
                          </Button>
                          {aluno.status === 'ERRO' && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => copiarDados(aluno, 'erro')}
                            >
                              {copiado === `${aluno.linha}-erro` ? (
                                <Check className="w-3 h-3 mr-1" />
                              ) : (
                                <Copy className="w-3 h-3 mr-1" />
                              )}
                              Copiar Msg de Erro
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default FormatadorPlanilhaPage;
