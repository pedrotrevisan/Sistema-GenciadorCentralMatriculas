import { useState } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { toast } from 'sonner';
import {
  MessageCircle,
  Send,
  Copy,
  ExternalLink,
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle,
  Sparkles
} from 'lucide-react';

// Templates de mensagem
const TEMPLATES = {
  documentos: {
    id: 'documentos',
    label: 'Solicitar Documentos',
    icon: FileText,
    color: 'text-blue-600',
    message: (data) => `Olá, ${data.nome}! 👋

Sou da equipe do SENAI CIMATEC e estou entrando em contato sobre sua matrícula no curso *${data.curso}*.

Para darmos continuidade ao processo, precisamos dos seguintes documentos:
📄 RG (frente e verso)
📄 CPF
📄 Comprovante de residência
📄 Comprovante de escolaridade

Por favor, envie as fotos ou PDFs dos documentos por aqui mesmo.

Caso tenha alguma dúvida, estou à disposição! 😊

*Protocolo: ${data.protocolo}*`
  },
  lembrete: {
    id: 'lembrete',
    label: 'Lembrete de Prazo',
    icon: Clock,
    color: 'text-amber-600',
    message: (data) => `Olá, ${data.nome}! 👋

Passando para lembrar que o prazo para envio dos documentos da sua matrícula no curso *${data.curso}* está próximo.

⏰ Por favor, envie os documentos pendentes o mais breve possível para garantir sua vaga.

Precisa de ajuda? É só responder esta mensagem!

*Protocolo: ${data.protocolo}*`
  },
  confirmacao: {
    id: 'confirmacao',
    label: 'Confirmar Matrícula',
    icon: CheckCircle,
    color: 'text-green-600',
    message: (data) => `Olá, ${data.nome}! 🎉

Ótima notícia! Sua matrícula no curso *${data.curso}* foi *APROVADA*!

📚 *Início das aulas:* [DATA]
📍 *Local:* SENAI CIMATEC
⏰ *Horário:* [HORÁRIO]

Em breve enviaremos mais informações sobre o primeiro dia de aula.

Bem-vindo(a) ao SENAI CIMATEC! 🚀

*Protocolo: ${data.protocolo}*`
  },
  pendencia: {
    id: 'pendencia',
    label: 'Resolver Pendência',
    icon: AlertTriangle,
    color: 'text-red-600',
    message: (data) => `Olá, ${data.nome}! 👋

Identificamos uma pendência na sua matrícula do curso *${data.curso}* que precisa ser resolvida:

⚠️ *Pendência:* [DESCREVER PENDÊNCIA]

Por favor, entre em contato conosco o mais rápido possível para regularizar a situação.

Estamos à disposição para ajudar!

*Protocolo: ${data.protocolo}*`
  },
  boasVindas: {
    id: 'boasVindas',
    label: 'Boas-vindas',
    icon: Sparkles,
    color: 'text-purple-600',
    message: (data) => `Olá, ${data.nome}! 👋

Seja muito bem-vindo(a) ao processo de matrícula do SENAI CIMATEC!

Recebemos sua inscrição para o curso *${data.curso}* e estamos muito felizes em tê-lo(a) conosco.

📋 Próximos passos:
1. Envie os documentos solicitados
2. Aguarde a análise
3. Receba a confirmação da matrícula

Qualquer dúvida, estamos aqui para ajudar! 😊

*Protocolo: ${data.protocolo}*`
  }
};

const CobrarZap = ({ pedido, variant = 'button' }) => {
  const [open, setOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('documentos');
  const [telefone, setTelefone] = useState('');
  const [mensagem, setMensagem] = useState('');
  const [editedMessage, setEditedMessage] = useState('');

  // Extrair dados do pedido
  const alunoNome = pedido?.alunos?.[0]?.nome || pedido?.aluno_nome || 'Aluno';
  const alunoTelefone = pedido?.alunos?.[0]?.telefone || pedido?.telefone || '';
  const cursoNome = pedido?.curso?.nome || pedido?.curso_nome || 'Curso';
  const protocolo = pedido?.protocolo || 'N/A';

  const handleOpen = () => {
    // Formatar telefone inicial
    let tel = alunoTelefone.replace(/\D/g, '');
    if (tel.length === 11 && !tel.startsWith('55')) {
      tel = '55' + tel;
    }
    setTelefone(tel);
    
    // Gerar mensagem inicial
    const template = TEMPLATES[selectedTemplate];
    const msg = template.message({
      nome: alunoNome.split(' ')[0], // Primeiro nome
      curso: cursoNome,
      protocolo: protocolo
    });
    setMensagem(msg);
    setEditedMessage(msg);
    setOpen(true);
  };

  const handleTemplateChange = (templateId) => {
    setSelectedTemplate(templateId);
    const template = TEMPLATES[templateId];
    const msg = template.message({
      nome: alunoNome.split(' ')[0],
      curso: cursoNome,
      protocolo: protocolo
    });
    setMensagem(msg);
    setEditedMessage(msg);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(editedMessage);
    toast.success('Mensagem copiada!');
  };

  const handleSend = () => {
    if (!telefone || telefone.length < 12) {
      toast.error('Digite um número de telefone válido com DDD');
      return;
    }

    // Formatar mensagem para URL
    const encodedMessage = encodeURIComponent(editedMessage);
    const whatsappUrl = `https://wa.me/${telefone}?text=${encodedMessage}`;
    
    // Abrir WhatsApp
    window.open(whatsappUrl, '_blank');
    
    toast.success('WhatsApp aberto!');
    setOpen(false);
  };

  const formatTelefone = (value) => {
    // Remover não-numéricos
    let digits = value.replace(/\D/g, '');
    
    // Adicionar 55 se necessário
    if (digits.length === 11 && !digits.startsWith('55')) {
      digits = '55' + digits;
    }
    
    setTelefone(digits);
  };

  // Renderização do botão
  if (variant === 'icon') {
    return (
      <>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleOpen}
          className="text-green-600 hover:text-green-700 hover:bg-green-50"
          title="Cobrar no Zap"
          data-testid="cobrar-zap-btn"
        >
          <MessageCircle className="h-4 w-4" />
        </Button>
        <CobrarZapModal 
          open={open} 
          setOpen={setOpen}
          telefone={telefone}
          setTelefone={formatTelefone}
          selectedTemplate={selectedTemplate}
          handleTemplateChange={handleTemplateChange}
          editedMessage={editedMessage}
          setEditedMessage={setEditedMessage}
          handleCopy={handleCopy}
          handleSend={handleSend}
          alunoNome={alunoNome}
        />
      </>
    );
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={handleOpen}
        className="text-green-600 border-green-200 hover:bg-green-50"
        data-testid="cobrar-zap-btn"
      >
        <MessageCircle className="h-4 w-4 mr-2" />
        Cobrar no Zap
      </Button>
      <CobrarZapModal 
        open={open} 
        setOpen={setOpen}
        telefone={telefone}
        setTelefone={formatTelefone}
        selectedTemplate={selectedTemplate}
        handleTemplateChange={handleTemplateChange}
        editedMessage={editedMessage}
        setEditedMessage={setEditedMessage}
        handleCopy={handleCopy}
        handleSend={handleSend}
        alunoNome={alunoNome}
      />
    </>
  );
};

// Modal separado para reutilização
const CobrarZapModal = ({
  open,
  setOpen,
  telefone,
  setTelefone,
  selectedTemplate,
  handleTemplateChange,
  editedMessage,
  setEditedMessage,
  handleCopy,
  handleSend,
  alunoNome
}) => {
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-green-600" />
            Cobrar no WhatsApp
          </DialogTitle>
          <DialogDescription>
            Envie uma mensagem para {alunoNome}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Telefone */}
          <div className="space-y-2">
            <Label>Telefone (com DDD)</Label>
            <div className="flex gap-2">
              <span className="flex items-center px-3 bg-gray-100 border rounded-l-md text-sm text-gray-600">
                +
              </span>
              <Input
                placeholder="5571999999999"
                value={telefone}
                onChange={(e) => setTelefone(e.target.value)}
                className="rounded-l-none"
                data-testid="telefone-input"
              />
            </div>
            <p className="text-xs text-gray-500">
              Formato: 55 + DDD + número (ex: 5571999999999)
            </p>
          </div>

          {/* Template */}
          <div className="space-y-2">
            <Label>Tipo de Mensagem</Label>
            <Select value={selectedTemplate} onValueChange={handleTemplateChange}>
              <SelectTrigger data-testid="template-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.values(TEMPLATES).map((template) => {
                  const Icon = template.icon;
                  return (
                    <SelectItem key={template.id} value={template.id}>
                      <div className="flex items-center gap-2">
                        <Icon className={`h-4 w-4 ${template.color}`} />
                        {template.label}
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          {/* Mensagem */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Mensagem</Label>
              <Button variant="ghost" size="sm" onClick={handleCopy}>
                <Copy className="h-3 w-3 mr-1" />
                Copiar
              </Button>
            </div>
            <Textarea
              value={editedMessage}
              onChange={(e) => setEditedMessage(e.target.value)}
              rows={10}
              className="font-mono text-sm"
              data-testid="mensagem-textarea"
            />
            <p className="text-xs text-gray-500">
              Você pode editar a mensagem antes de enviar
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSend}
            className="bg-green-600 hover:bg-green-700"
            data-testid="enviar-zap-btn"
          >
            <Send className="h-4 w-4 mr-2" />
            Abrir WhatsApp
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CobrarZap;
