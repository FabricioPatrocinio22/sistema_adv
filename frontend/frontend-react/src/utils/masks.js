// src/utils/masks.js

// 1. MÁSCARA PARA CPF E CNPJ (Híbrida)
export const maskDocumento = (value) => {
    if (!value) return ""
    
    // Remove tudo que não é número
    value = value.replace(/\D/g, "")
  
    // Limita ao tamanho do CNPJ (14 dígitos)
    if (value.length > 14) {
      value = value.slice(0, 14)
    }
  
    // Se tiver até 11 dígitos, aplica máscara de CPF: 000.000.000-00
    if (value.length <= 11) {
      return value
        .replace(/(\d{3})(\d)/, "$1.$2")
        .replace(/(\d{3})(\d)/, "$1.$2")
        .replace(/(\d{3})(\d{1,2})/, "$1-$2")
        .replace(/(-\d{2})\d+?$/, "$1")
    } 
    
    // Se tiver mais que 11, vira CNPJ: 00.000.000/0000-00
    return value
      .replace(/^(\d{2})(\d)/, "$1.$2")
      .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1/$2")
      .replace(/(\d{4})(\d)/, "$1-$2")
  }
  
  // 2. MÁSCARA PARA TELEFONE (Celular e Fixo)
  export const maskTelefone = (value) => {
    if (!value) return ""
    
    value = value.replace(/\D/g, "")
    
    // Limita a 11 dígitos
    if (value.length > 11) {
      value = value.slice(0, 11)
    }
  
    // (00) 00000-0000
    return value
      .replace(/^(\d{2})(\d)/g, "($1) $2")
      .replace(/(\d)(\d{4})$/, "$1-$2")
  }

  // 3. MÁSCARA PARA DINHEIRO (R$)
  export const maskMoeda = (value) => {
    if (!value) return ""
    
    value = value.replace(/\D/g, "") // Remove tudo que não é dígito
    value = (Number(value) / 100).toFixed(2) + "" // Divide por 100 para ter centavos
    value = value.replace(".", ",") // Troca ponto por vírgula
    value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.") // Coloca ponto nos milhares
    return `R$ ${value}`
  }