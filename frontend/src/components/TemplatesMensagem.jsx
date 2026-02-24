import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { toast } from 'sonner';
import { 
  Mail, MessageCircle, Send, Copy, ExternalLink, 
  FileText, RefreshCw, Check, Loader2
} from 'lucide-react';
import api from '../services/api';

/**
 * Componente para gerar e enviar mensagens usando templates
 * Integra com os endpoints /api/regras/templates/*
 */
const TemplatesMensagem = ({
  pedido, // Dados do pedido para preencher o template
  aluno,  // Dados do aluno
  documentosFaltantes = [],
  onEmailSent,
  onWhatsAppOpen
}) => {
  const [templates, setTemplates] = useState({ email: [], whatsapp: [] });
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [mensagemGerada, setMensagemGerada] = useState(null);
  const [loading, setLoading] = useState(false);
  const [telefone, setTelefone] = useState(aluno?.telefone || '');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    carregarTemplates();
  }, []);

  const carregarTemplates = async () => {
    try {
      const [emailRes, whatsappRes] = await Promise.all([
        api.get('/regras/templates/email'),
        api.get('/regras/templates/whatsapp')
      ]);
      setTemplates({
        email: emailRes.data.templates,
        whatsapp: whatsappRes.data.templates
      });
    } catch (error) {
      console.error('Erro ao carregar templates:', error);
    }
  };

  const prepararDados = () => {
    // Preparar dados para substituição no template
    const docsListaHtml = documentosFaltantes
      .map(doc => `<li>${doc.replace(/_/g, ' ')}</li>`)
      .join('\n');
    
    const docsListaTexto = documentosFaltantes
      .map(doc => `• ${doc.replace(/_/g, ' ')}`)
      .join('\n');

    return {
      aluno_nome: aluno?.nome || 'Aluno',
      curso_nome: pedido?.curso_nome || 'Curso',
      protocolo: pedido?.numero_protocolo || pedido?.id?.substring(0, 8) || 'N/A',
      dias_restantes: '5', // Pode ser calculado dinamicamente
      documentos_lista: docsListaHtml,
      documentos_lista_texto: docsListaTexto,
      prazo_texto: 'HOJE',
      turma: pedido?.turma_nome || 'A definir',
      data_inicio: pedido?.data_inicio || 'A definir',
      horario: pedido?.horario || 'A definir',
      local: 'SENAI CIMATEC',
      link_portal: 'https://portal.senai.br',
      valor: pedido?.valor || '0,00',
      data_vencimento: 'A definir',
      forma_pagamento: 'Boleto',
      dados_boleto: '',
      dados_boleto_texto: '',
      info_pagamento: '',
      info_pagamento_texto: '',
      motivo: pedido?.motivo_rejeicao || 'Não atende aos pré-requisitos do curso'
    };
  };

  const gerarMensagemEmail = async (tipo) => {
    setLoading(true);
    try {
      const dados = prepararDados();
      const response = await api.post('/regras/templates/email/render', {
        tipo,
        dados,
        formato: 'html'
      });
      setMensagemGerada({
        tipo: 'email',
        template: tipo,
        ...response.data
      });
    } catch (error) {
      toast.error('Erro ao gerar template: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const gerarMensagemWhatsApp = async (tipo) => {
    setLoading(true);
    try {
      const dados = prepararDados();
      const response = await api.post('/regras/templates/whatsapp/render', {
        tipo,
        dados,
        telefone: telefone
      });
      setMensagemGerada({
        tipo: 'whatsapp',
        template: tipo,
        ...response.data
      });
    } catch (error) {
      toast.error('Erro ao gerar template: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const copiarMensagem = () => {
    const texto = mensagemGerada.tipo === 'email' 
      ? mensagemGerada.corpo.replace(/<[^>]*>/g, '') // Remove HTML
      : mensagemGerada.mensagem;
    
    navigator.clipboard.writeText(texto);
    setCopied(true);
    toast.success('Mensagem copiada!');
    setTimeout(() => setCopied(false), 2000);
  };

  const abrirWhatsApp = () => {
    if (mensagemGerada?.link_whatsapp) {
      window.open(mensagemGerada.link_whatsapp, '_blank');
      if (onWhatsAppOpen) onWhatsAppOpen(mensagemGerada);
    }
  };

  const getTemplateLabel = (nome) => {
    const labels = {
      'documentos_pendentes': 'Documentos Pendentes',
      'prazo_expirando': 'Prazo Expirando',
      'confirmacao_matricula': 'Confirmação de Matrícula',
      'aguardando_pagamento': 'Aguardando Pagamento',
      'nao_atende_requisito': 'Não Atende Requisito',
      'lembrete_documentos': 'Lembrete de Documentos'
    };
    return labels[nome] || nome.replace(/_/g, ' ');
  };

  return (
    <Card data-testid="templates-mensagem">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-green-600" />
          Templates de Mensagem
        </CardTitle>
        <CardDescription>
          Gere mensagens padronizadas para comunicação com o aluno
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="whatsapp">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="whatsapp" className="flex items-center gap-2">
              <MessageCircle className="w-4 h-4" />
              WhatsApp
            </TabsTrigger>
            <TabsTrigger value="email" className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              E-mail
            </TabsTrigger>
          </TabsList>

          {/* Tab WhatsApp */}
          <TabsContent value="whatsapp" className="space-y-4">
            <div className="space-y-2">
              <Label>Telefone do Aluno</Label>
              <Input
                placeholder="(71) 99999-9999"
                value={telefone}
                onChange={(e) => setTelefone(e.target.value)}
                data-testid="input-telefone"
              />
            </div>

            <div className="space-y-2">
              <Label>Selecione o Template</Label>
              <div className="grid grid-cols-2 gap-2">
                {templates.whatsapp.map((template) => (
                  <Button
                    key={template.nome}
                    variant={selectedTemplate === template.nome ? "default" : "outline"}
                    size="sm"
                    className="justify-start"
                    onClick={() => {
                      setSelectedTemplate(template.nome);
                      gerarMensagemWhatsApp(template.nome);
                    }}
                    data-testid={`btn-template-${template.nome}`}
                  >
                    {getTemplateLabel(template.nome)}
                  </Button>
                ))}
              </div>
            </div>

            {loading && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-6 h-6 animate-spin" />
              </div>
            )}

            {mensagemGerada?.tipo === 'whatsapp' && (
              <div className="space-y-3">
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <pre className="whitespace-pre-wrap text-sm font-sans">
                    {mensagemGerada.mensagem}
                  </pre>
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={copiarMensagem}
                    data-testid="btn-copiar"
                  >
                    {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                    {copied ? 'Copiado!' : 'Copiar'}
                  </Button>
                  
                  {mensagemGerada.link_whatsapp && (
                    <Button 
                      size="sm" 
                      className="bg-green-600 hover:bg-green-700"
                      onClick={abrirWhatsApp}
                      data-testid="btn-abrir-whatsapp"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Abrir WhatsApp
                    </Button>
                  )}
                </div>
              </div>
            )}
          </TabsContent>

          {/* Tab Email */}
          <TabsContent value="email" className="space-y-4">
            <div className="space-y-2">
              <Label>Selecione o Template</Label>
              <div className="grid grid-cols-2 gap-2">
                {templates.email.map((template) => (
                  <Button
                    key={template.nome}
                    variant={selectedTemplate === template.nome ? "default" : "outline"}
                    size="sm"
                    className="justify-start"
                    onClick={() => {
                      setSelectedTemplate(template.nome);
                      gerarMensagemEmail(template.nome);
                    }}
                    data-testid={`btn-template-email-${template.nome}`}
                  >
                    {getTemplateLabel(template.nome)}
                  </Button>
                ))}
              </div>
            </div>

            {loading && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-6 h-6 animate-spin" />
              </div>
            )}

            {mensagemGerada?.tipo === 'email' && (
              <div className="space-y-3">
                <div className="p-2 bg-slate-100 rounded-lg">
                  <p className="text-sm"><strong>Assunto:</strong> {mensagemGerada.assunto}</p>
                </div>
                
                <div className="p-4 bg-white rounded-lg border max-h-96 overflow-y-auto">
                  <div 
                    className="prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: mensagemGerada.corpo }}
                  />
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={copiarMensagem}
                  >
                    {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                    {copied ? 'Copiado!' : 'Copiar Texto'}
                  </Button>
                  
                  <Button 
                    size="sm"
                    onClick={() => {
                      const mailto = `mailto:${aluno?.email || ''}?subject=${encodeURIComponent(mensagemGerada.assunto)}`;
                      window.open(mailto, '_blank');
                    }}
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Abrir no E-mail
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default TemplatesMensagem;
