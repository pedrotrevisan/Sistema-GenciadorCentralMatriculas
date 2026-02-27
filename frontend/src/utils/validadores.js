/**
 * Utilitários de validação de documentos brasileiros
 */

/**
 * Valida CPF usando o algoritmo oficial dos dígitos verificadores
 * @param {string} cpf - CPF com ou sem formatação
 * @returns {object} { valido: boolean, mensagem: string, cpfFormatado: string }
 */
export const validarCPF = (cpf) => {
  // Remove caracteres não numéricos
  const cpfLimpo = cpf.replace(/\D/g, '');
  
  // Verifica se tem 11 dígitos
  if (cpfLimpo.length !== 11) {
    return {
      valido: false,
      mensagem: 'CPF deve ter 11 dígitos',
      cpfFormatado: cpf
    };
  }
  
  // Verifica se todos os dígitos são iguais (CPFs inválidos conhecidos)
  if (/^(\d)\1{10}$/.test(cpfLimpo)) {
    return {
      valido: false,
      mensagem: 'CPF inválido (dígitos repetidos)',
      cpfFormatado: formatarCPF(cpfLimpo)
    };
  }
  
  // Calcula primeiro dígito verificador
  let soma = 0;
  for (let i = 0; i < 9; i++) {
    soma += parseInt(cpfLimpo.charAt(i)) * (10 - i);
  }
  let resto = (soma * 10) % 11;
  if (resto === 10 || resto === 11) resto = 0;
  if (resto !== parseInt(cpfLimpo.charAt(9))) {
    return {
      valido: false,
      mensagem: 'CPF inválido (dígito verificador incorreto)',
      cpfFormatado: formatarCPF(cpfLimpo)
    };
  }
  
  // Calcula segundo dígito verificador
  soma = 0;
  for (let i = 0; i < 10; i++) {
    soma += parseInt(cpfLimpo.charAt(i)) * (11 - i);
  }
  resto = (soma * 10) % 11;
  if (resto === 10 || resto === 11) resto = 0;
  if (resto !== parseInt(cpfLimpo.charAt(10))) {
    return {
      valido: false,
      mensagem: 'CPF inválido (dígito verificador incorreto)',
      cpfFormatado: formatarCPF(cpfLimpo)
    };
  }
  
  return {
    valido: true,
    mensagem: 'CPF válido',
    cpfFormatado: formatarCPF(cpfLimpo)
  };
};

/**
 * Formata CPF para exibição (000.000.000-00)
 * @param {string} cpf - CPF sem formatação
 * @returns {string} CPF formatado
 */
export const formatarCPF = (cpf) => {
  const cpfLimpo = cpf.replace(/\D/g, '');
  if (cpfLimpo.length !== 11) return cpf;
  return cpfLimpo.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
};

/**
 * Máscara de CPF para input (formata enquanto digita)
 * @param {string} value - Valor atual do input
 * @returns {string} Valor formatado
 */
export const mascaraCPF = (value) => {
  const cpfLimpo = value.replace(/\D/g, '').slice(0, 11);
  
  if (cpfLimpo.length <= 3) return cpfLimpo;
  if (cpfLimpo.length <= 6) return `${cpfLimpo.slice(0, 3)}.${cpfLimpo.slice(3)}`;
  if (cpfLimpo.length <= 9) return `${cpfLimpo.slice(0, 3)}.${cpfLimpo.slice(3, 6)}.${cpfLimpo.slice(6)}`;
  return `${cpfLimpo.slice(0, 3)}.${cpfLimpo.slice(3, 6)}.${cpfLimpo.slice(6, 9)}-${cpfLimpo.slice(9)}`;
};

/**
 * Valida CNPJ usando o algoritmo oficial
 * @param {string} cnpj - CNPJ com ou sem formatação
 * @returns {object} { valido: boolean, mensagem: string }
 */
export const validarCNPJ = (cnpj) => {
  const cnpjLimpo = cnpj.replace(/\D/g, '');
  
  if (cnpjLimpo.length !== 14) {
    return { valido: false, mensagem: 'CNPJ deve ter 14 dígitos' };
  }
  
  if (/^(\d)\1{13}$/.test(cnpjLimpo)) {
    return { valido: false, mensagem: 'CNPJ inválido' };
  }
  
  // Validação dos dígitos verificadores
  let tamanho = cnpjLimpo.length - 2;
  let numeros = cnpjLimpo.substring(0, tamanho);
  const digitos = cnpjLimpo.substring(tamanho);
  let soma = 0;
  let pos = tamanho - 7;
  
  for (let i = tamanho; i >= 1; i--) {
    soma += parseInt(numeros.charAt(tamanho - i)) * pos--;
    if (pos < 2) pos = 9;
  }
  
  let resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
  if (resultado !== parseInt(digitos.charAt(0))) {
    return { valido: false, mensagem: 'CNPJ inválido' };
  }
  
  tamanho = tamanho + 1;
  numeros = cnpjLimpo.substring(0, tamanho);
  soma = 0;
  pos = tamanho - 7;
  
  for (let i = tamanho; i >= 1; i--) {
    soma += parseInt(numeros.charAt(tamanho - i)) * pos--;
    if (pos < 2) pos = 9;
  }
  
  resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
  if (resultado !== parseInt(digitos.charAt(1))) {
    return { valido: false, mensagem: 'CNPJ inválido' };
  }
  
  return { valido: true, mensagem: 'CNPJ válido' };
};

/**
 * Formata telefone para exibição
 * @param {string} telefone - Telefone sem formatação
 * @returns {string} Telefone formatado
 */
export const formatarTelefone = (telefone) => {
  const telLimpo = telefone.replace(/\D/g, '');
  
  if (telLimpo.length === 11) {
    return telLimpo.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }
  if (telLimpo.length === 10) {
    return telLimpo.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }
  return telefone;
};

/**
 * Máscara de telefone para input
 * @param {string} value - Valor atual do input
 * @returns {string} Valor formatado
 */
export const mascaraTelefone = (value) => {
  const telLimpo = value.replace(/\D/g, '').slice(0, 11);
  
  if (telLimpo.length <= 2) return telLimpo.length ? `(${telLimpo}` : '';
  if (telLimpo.length <= 6) return `(${telLimpo.slice(0, 2)}) ${telLimpo.slice(2)}`;
  if (telLimpo.length <= 10) return `(${telLimpo.slice(0, 2)}) ${telLimpo.slice(2, 6)}-${telLimpo.slice(6)}`;
  return `(${telLimpo.slice(0, 2)}) ${telLimpo.slice(2, 7)}-${telLimpo.slice(7)}`;
};
