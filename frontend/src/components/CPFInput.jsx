import { useState, useEffect } from 'react';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { CheckCircle2, XCircle, AlertTriangle, Copy, Check } from 'lucide-react';
import { validarCPF, mascaraCPF } from '../utils/validadores';
import { cn } from '../lib/utils';
import { toast } from 'sonner';

/**
 * Input de CPF com validação em tempo real
 * - Máscara automática (000.000.000-00)
 * - Validação do algoritmo oficial
 * - Feedback visual instantâneo
 * - Botão para copiar template de erro
 */
const CPFInput = ({ 
  value, 
  onChange, 
  onValidationChange,
  disabled = false,
  placeholder = "000.000.000-00",
  nomeAluno = "",
  ...props 
}) => {
  const [validacao, setValidacao] = useState(null);
  const [touched, setTouched] = useState(false);
  const [copiado, setCopiado] = useState(false);

  // Template de mensagem para CPF inválido
  const templateCPFInvalido = `CPF INVÁLIDO - ${nomeAluno || 'ALUNO'}

O CPF informado está inválido no validador. Para prosseguir com a matrícula, preciso do CPF correto (11 dígitos).

Por favor, confirme:
• CPF correto do aluno/titular
• Se o aluno é maior ou menor de 18 anos
• Se menor, dados do responsável financeiro

Aguardo retorno.`;

  // Validar CPF quando valor muda
  useEffect(() => {
    if (!value || value.replace(/\D/g, '').length === 0) {
      setValidacao(null);
      return;
    }

    const cpfLimpo = value.replace(/\D/g, '');
    
    // Só valida se tiver 11 dígitos
    if (cpfLimpo.length === 11) {
      const resultado = validarCPF(value);
      setValidacao(resultado);
    } else if (cpfLimpo.length > 0 && touched) {
      setValidacao({
        valido: false,
        mensagem: `CPF incompleto (${cpfLimpo.length}/11 dígitos)`,
        cpfFormatado: value
      });
    }
  }, [value, touched]);

  // Notificar parent sobre mudança na validação (separado para evitar loop)
  useEffect(() => {
    if (onValidationChange && validacao !== null) {
      onValidationChange(validacao);
    }
  }, [validacao?.valido]); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle input change com máscara
  const handleChange = (e) => {
    const valorFormatado = mascaraCPF(e.target.value);
    onChange(valorFormatado);
  };

  // Copiar template de erro
  const copiarTemplate = async () => {
    try {
      await navigator.clipboard.writeText(templateCPFInvalido);
      setCopiado(true);
      toast.success('Template copiado! Cole no chamado.');
      setTimeout(() => setCopiado(false), 2000);
    } catch (err) {
      toast.error('Erro ao copiar');
    }
  };

  return (
    <div className="space-y-2">
      <div className="relative">
        <Input
          type="text"
          value={value}
          onChange={handleChange}
          onBlur={() => setTouched(true)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "pr-10",
            validacao?.valido === true && "border-green-500 bg-green-50/50",
            validacao?.valido === false && touched && "border-red-500 bg-red-50/50"
          )}
          data-testid="cpf-input"
          {...props}
        />
        
        {/* Ícone de status */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          {validacao?.valido === true && (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          )}
          {validacao?.valido === false && touched && (
            <XCircle className="h-5 w-5 text-red-500" />
          )}
        </div>
      </div>

      {/* Feedback de validação */}
      {validacao && touched && (
        <div className={cn(
          "flex items-center justify-between p-2 rounded-md text-sm",
          validacao.valido 
            ? "bg-green-100 text-green-700" 
            : "bg-red-100 text-red-700"
        )}>
          <div className="flex items-center gap-2">
            {validacao.valido ? (
              <>
                <CheckCircle2 className="h-4 w-4" />
                <span>CPF válido</span>
              </>
            ) : (
              <>
                <AlertTriangle className="h-4 w-4" />
                <span>{validacao.mensagem}</span>
              </>
            )}
          </div>
          
          {/* Botão para copiar template quando CPF inválido */}
          {!validacao.valido && (
            <button
              type="button"
              onClick={copiarTemplate}
              className="flex items-center gap-1 px-2 py-1 bg-red-200 hover:bg-red-300 rounded text-xs font-medium transition-colors"
              title="Copiar template de mensagem"
            >
              {copiado ? (
                <>
                  <Check className="h-3 w-3" />
                  Copiado!
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  Copiar Template
                </>
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default CPFInput;
