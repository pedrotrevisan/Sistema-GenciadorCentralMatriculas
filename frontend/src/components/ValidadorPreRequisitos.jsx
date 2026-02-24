import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { 
  CheckCircle, XCircle, AlertTriangle, User, GraduationCap,
  FileText, Building, Calendar, Loader2, RefreshCw
} from 'lucide-react';
import api from '../services/api';

/**
 * Componente para validar pré-requisitos de matrícula
 * Integra com o endpoint /api/regras/validar/completo
 */
const ValidadorPreRequisitos = ({
  dataNascimento,
  escolaridade,
  documentos = [],
  tipoCurso,
  isPcd = false,
  isMenor = false,
  temEmpresa = false,
  onValidationComplete,
  autoValidate = false
}) => {
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (autoValidate && dataNascimento && tipoCurso) {
      validar();
    }
  }, [dataNascimento, escolaridade, documentos, tipoCurso, isPcd, isMenor, temEmpresa, autoValidate]);

  const validar = async () => {
    if (!dataNascimento || !tipoCurso) {
      setError('Data de nascimento e tipo de curso são obrigatórios');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/regras/validar/completo', {
        data_nascimento: dataNascimento,
        escolaridade: escolaridade || 'fundamental_incompleto',
        documentos: documentos,
        tipo_curso: tipoCurso,
        is_pcd: isPcd,
        is_menor: isMenor,
        tem_empresa: temEmpresa
      });

      setResultado(response.data);
      
      if (onValidationComplete) {
        onValidationComplete(response.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao validar pré-requisitos');
    } finally {
      setLoading(false);
    }
  };

  const StatusIcon = ({ valido }) => {
    if (valido) {
      return <CheckCircle className="w-5 h-5 text-green-600" />;
    }
    return <XCircle className="w-5 h-5 text-red-600" />;
  };

  if (loading) {
    return (
      <Card data-testid="validador-loading">
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3">Validando pré-requisitos...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" data-testid="validador-error">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Erro na Validação</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
        <Button variant="outline" size="sm" onClick={validar} className="mt-2">
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar Novamente
        </Button>
      </Alert>
    );
  }

  if (!resultado) {
    return (
      <Card data-testid="validador-inicial">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-blue-600" />
            Validação de Pré-Requisitos
          </CardTitle>
          <CardDescription>
            Verifique se o aluno atende aos requisitos do curso
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={validar} disabled={!dataNascimento || !tipoCurso}>
            Validar Pré-Requisitos
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="validador-resultado">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              {resultado.aprovado ? (
                <CheckCircle className="w-6 h-6 text-green-600" />
              ) : (
                <AlertTriangle className="w-6 h-6 text-red-600" />
              )}
              {resultado.aprovado ? 'Pré-Requisitos Atendidos' : 'Pré-Requisitos Não Atendidos'}
            </CardTitle>
            <CardDescription>
              {resultado.tipo_curso_descricao}
            </CardDescription>
          </div>
          <Badge 
            variant={resultado.aprovado ? "default" : "destructive"}
            className={resultado.aprovado ? "bg-green-600" : ""}
          >
            {resultado.status_sugerido === 'aprovado' ? 'APROVADO' : 'NÃO ATENDE'}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Validação de Idade */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
          <StatusIcon valido={resultado.validacao_idade.valido} />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-slate-500" />
              <span className="font-medium">Idade</span>
            </div>
            <p className="text-sm text-slate-600 mt-1">
              Aluno tem {resultado.validacao_idade.idade} anos
              {resultado.validacao_idade.idade_minima && 
                ` (mín: ${resultado.validacao_idade.idade_minima}`}
              {resultado.validacao_idade.idade_maxima && 
                `, máx: ${resultado.validacao_idade.idade_maxima}`}
              {resultado.validacao_idade.idade_minima && ')'}
              {resultado.validacao_idade.is_pcd && ' - PCD'}
            </p>
            {resultado.validacao_idade.erros?.map((erro, i) => (
              <p key={i} className="text-sm text-red-600 mt-1">{erro}</p>
            ))}
          </div>
        </div>

        {/* Validação de Escolaridade */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
          <StatusIcon valido={resultado.validacao_escolaridade.valido} />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <GraduationCap className="w-4 h-4 text-slate-500" />
              <span className="font-medium">Escolaridade</span>
            </div>
            <p className="text-sm text-slate-600 mt-1">
              {resultado.validacao_escolaridade.escolaridade_aluno?.replace(/_/g, ' ')}
              {resultado.validacao_escolaridade.escolaridade_minima && 
                ` (mín: ${resultado.validacao_escolaridade.escolaridade_minima.replace(/_/g, ' ')})`}
            </p>
            {resultado.validacao_escolaridade.erro && (
              <p className="text-sm text-red-600 mt-1">{resultado.validacao_escolaridade.erro}</p>
            )}
          </div>
        </div>

        {/* Validação de Documentos */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
          <StatusIcon valido={resultado.validacao_documentos.valido} />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-500" />
                <span className="font-medium">Documentos</span>
              </div>
              <span className="text-sm text-slate-500">
                {Math.round(resultado.validacao_documentos.percentual_completo)}% completo
              </span>
            </div>
            <Progress 
              value={resultado.validacao_documentos.percentual_completo} 
              className="h-2 mt-2"
            />
            
            {resultado.validacao_documentos.documentos_faltantes?.length > 0 && (
              <div className="mt-2">
                <p className="text-sm font-medium text-red-600">Documentos faltantes:</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {resultado.validacao_documentos.documentos_faltantes.map((doc, i) => (
                    <Badge key={i} variant="outline" className="text-xs border-red-300 text-red-600">
                      {doc.replace(/_/g, ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Validação de Empresa */}
        {!resultado.validacao_empresa.valido && (
          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
            <StatusIcon valido={false} />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <Building className="w-4 h-4 text-slate-500" />
                <span className="font-medium">Vínculo com Empresa</span>
              </div>
              <p className="text-sm text-red-600 mt-1">{resultado.validacao_empresa.erro}</p>
            </div>
          </div>
        )}

        <Separator />

        {/* Resumo de Erros */}
        {resultado.erros?.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Problemas Encontrados</AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside mt-2 space-y-1">
                {resultado.erros.map((erro, i) => (
                  <li key={i} className="text-sm">{erro}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Ações */}
        <div className="flex gap-2 justify-end">
          <Button variant="outline" size="sm" onClick={validar}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Revalidar
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default ValidadorPreRequisitos;
