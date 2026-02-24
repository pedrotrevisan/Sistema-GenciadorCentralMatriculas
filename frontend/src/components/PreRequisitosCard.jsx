import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  GraduationCap, 
  Calendar, 
  FileText,
  Users,
  Loader2,
  Info
} from 'lucide-react';
import { cn } from '../lib/utils';
import api from '../services/api';

/**
 * Componente que exibe os pré-requisitos do curso selecionado
 * e valida em tempo real se o aluno atende aos requisitos
 */
const PreRequisitosCard = ({ 
  cursoId, 
  cursoTipo,
  dataNascimento,
  escolaridade,
  isPcd = false,
  isMenor = false,
  onValidationChange
}) => {
  const [requisitos, setRequisitos] = useState(null);
  const [validacao, setValidacao] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tiposCurso, setTiposCurso] = useState([]);

  // Buscar tipos de curso disponíveis
  useEffect(() => {
    const fetchTipos = async () => {
      try {
        const response = await api.get('/regras/tipos-curso');
        setTiposCurso(response.data);
      } catch (err) {
        console.error('Erro ao buscar tipos de curso:', err);
      }
    };
    fetchTipos();
  }, []);

  // Buscar requisitos do tipo de curso
  useEffect(() => {
    const fetchRequisitos = async () => {
      if (!cursoTipo) {
        setRequisitos(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await api.get(`/regras/tipos-curso/${cursoTipo}`);
        setRequisitos(response.data);
      } catch (err) {
        console.error('Erro ao buscar requisitos:', err);
        setError('Não foi possível carregar os requisitos do curso');
        setRequisitos(null);
      } finally {
        setLoading(false);
      }
    };

    fetchRequisitos();
  }, [cursoTipo]);

  // Validar idade quando data de nascimento muda
  useEffect(() => {
    const validarIdade = async () => {
      if (!cursoTipo || !dataNascimento) {
        setValidacao(prev => ({ ...prev, idade: null }));
        return;
      }

      try {
        const response = await api.post('/regras/validar/idade', {
          data_nascimento: dataNascimento,
          tipo_curso: cursoTipo,
          is_pcd: isPcd
        });
        setValidacao(prev => ({ ...prev, idade: response.data }));
      } catch (err) {
        console.error('Erro na validação de idade:', err);
      }
    };

    validarIdade();
  }, [cursoTipo, dataNascimento, isPcd]);

  // Validar escolaridade
  useEffect(() => {
    const validarEscolaridade = async () => {
      if (!cursoTipo || !escolaridade) {
        setValidacao(prev => ({ ...prev, escolaridade: null }));
        return;
      }

      try {
        const response = await api.post(
          `/regras/validar/escolaridade?escolaridade=${escolaridade}&tipo_curso=${cursoTipo}`
        );
        setValidacao(prev => ({ ...prev, escolaridade: response.data }));
      } catch (err) {
        console.error('Erro na validação de escolaridade:', err);
      }
    };

    validarEscolaridade();
  }, [cursoTipo, escolaridade]);

  // Notificar mudanças na validação
  useEffect(() => {
    if (onValidationChange) {
      const isValid = validacao?.idade?.valido !== false && 
                     validacao?.escolaridade?.valido !== false;
      onValidationChange(isValid, validacao);
    }
  }, [validacao, onValidationChange]);

  if (!cursoId) {
    return null;
  }

  if (loading) {
    return (
      <Card className="border-slate-200 bg-slate-50">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Carregando requisitos...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Se o curso não tem tipo definido, mostrar card informativo
  if (!cursoTipo) {
    return (
      <Card className="border-amber-200 bg-amber-50/50" data-testid="pre-requisitos-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-amber-600" />
              Pré-Requisitos do Curso
            </CardTitle>
            <Badge variant="outline" className="border-amber-300 text-amber-700 bg-amber-100">
              <Info className="h-3 w-3 mr-1" />
              Tipo não definido
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <Alert className="bg-amber-100 border-amber-300">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              Este curso ainda não tem um <strong>tipo de curso</strong> configurado. 
              Sem essa informação, não é possível validar pré-requisitos como idade mínima/máxima e escolaridade exigida.
            </AlertDescription>
          </Alert>
          <p className="text-sm text-slate-600">
            A solicitação pode prosseguir, mas recomenda-se configurar o tipo do curso no cadastro para habilitar a validação automática de pré-requisitos.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="bg-red-50 border-red-200">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!requisitos) {
    return null;
  }

  // Determinar status geral
  const hasIdadeIssue = validacao?.idade?.valido === false;
  const hasEscolaridadeIssue = validacao?.escolaridade?.valido === false;
  const hasAnyIssue = hasIdadeIssue || hasEscolaridadeIssue;

  return (
    <Card className={cn(
      "transition-all duration-300",
      hasAnyIssue 
        ? "border-red-300 bg-red-50/50" 
        : validacao?.idade?.valido && validacao?.escolaridade?.valido
          ? "border-green-300 bg-green-50/50"
          : "border-blue-200 bg-blue-50/50"
    )} data-testid="pre-requisitos-card">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-blue-600" />
            Pré-Requisitos do Curso
          </CardTitle>
          {hasAnyIssue ? (
            <Badge variant="destructive" className="bg-red-500">
              <XCircle className="h-3 w-3 mr-1" />
              Não Atende
            </Badge>
          ) : validacao?.idade?.valido && validacao?.escolaridade?.valido ? (
            <Badge className="bg-green-500">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Atende
            </Badge>
          ) : (
            <Badge variant="outline" className="border-blue-300 text-blue-700">
              <Info className="h-3 w-3 mr-1" />
              Aguardando Dados
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Idade */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Calendar className="h-4 w-4" />
            Idade
            {validacao?.idade?.valido === true && (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            )}
            {validacao?.idade?.valido === false && (
              <XCircle className="h-4 w-4 text-red-500" />
            )}
          </div>
          <div className="pl-6 space-y-1">
            {requisitos.idade_minima && requisitos.idade_maxima ? (
              <p className="text-sm text-slate-600">
                Faixa etária: <span className="font-medium">{requisitos.idade_minima} a {requisitos.idade_maxima} anos</span>
              </p>
            ) : requisitos.idade_minima ? (
              <p className="text-sm text-slate-600">
                Idade mínima: <span className="font-medium">{requisitos.idade_minima} anos</span>
              </p>
            ) : (
              <p className="text-sm text-slate-500 italic">Sem restrição de idade</p>
            )}
            
            {validacao?.idade && (
              <div className={cn(
                "text-sm p-2 rounded",
                validacao.idade.valido 
                  ? "bg-green-100 text-green-700" 
                  : "bg-red-100 text-red-700"
              )}>
                {validacao.idade.valido ? (
                  <span>✓ Idade do aluno ({validacao.idade.idade_atual} anos) está dentro do permitido</span>
                ) : (
                  <span>✗ {validacao.idade.motivo || 'Idade fora da faixa permitida'}</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Escolaridade */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <FileText className="h-4 w-4" />
            Escolaridade Mínima
            {validacao?.escolaridade?.valido === true && (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            )}
            {validacao?.escolaridade?.valido === false && (
              <XCircle className="h-4 w-4 text-red-500" />
            )}
          </div>
          <div className="pl-6 space-y-1">
            <p className="text-sm text-slate-600">
              Exigido: <span className="font-medium">{requisitos.escolaridade_label || requisitos.escolaridade || 'Não especificado'}</span>
            </p>
            
            {validacao?.escolaridade && (
              <div className={cn(
                "text-sm p-2 rounded",
                validacao.escolaridade.valido 
                  ? "bg-green-100 text-green-700" 
                  : "bg-red-100 text-red-700"
              )}>
                {validacao.escolaridade.valido ? (
                  <span>✓ Escolaridade do aluno atende ao requisito</span>
                ) : (
                  <span>✗ {validacao.escolaridade.motivo || 'Escolaridade abaixo do exigido'}</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Documentos Obrigatórios */}
        {requisitos.documentos && requisitos.documentos.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
              <Users className="h-4 w-4" />
              Documentos Obrigatórios
            </div>
            <div className="pl-6">
              <ul className="text-sm text-slate-600 space-y-1">
                {requisitos.documentos.slice(0, 5).map((doc, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-slate-400 mt-0.5">•</span>
                    <span>{typeof doc === 'object' ? doc.nome : doc}</span>
                  </li>
                ))}
                {requisitos.documentos.length > 5 && (
                  <li className="text-slate-500 italic">
                    ... e mais {requisitos.documentos.length - 5} documentos
                  </li>
                )}
              </ul>
            </div>
          </div>
        )}

        {/* Alerta se não atende */}
        {hasAnyIssue && (
          <Alert variant="destructive" className="bg-red-100 border-red-300">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Atenção:</strong> O aluno não atende aos pré-requisitos. 
              A solicitação será marcada como "Não Atende Requisito" e cancelada automaticamente.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default PreRequisitosCard;
