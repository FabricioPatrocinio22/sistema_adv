import { useEffect, useState, useRef } from 'react'
import { 
  Box, Heading, Table, Thead, Tbody, Tr, Th, Td, Badge, Button, Flex, 
  IconButton, useToast, Skeleton, Text, Container,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalFooter, ModalBody, ModalCloseButton,
  FormControl, FormLabel, Input, Select, useDisclosure, VStack,
  Drawer, DrawerBody, DrawerFooter, DrawerHeader, DrawerOverlay, DrawerContent, DrawerCloseButton,
  Divider, Spinner, HStack, Tabs, TabList, TabPanels, Tab, TabPanel, Avatar, Textarea
} from '@chakra-ui/react'
import { FiPlus, FiTrash2, FiCpu, FiUpload, FiFileText, FiZap, FiSend } from 'react-icons/fi' 
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import Sidebar from './components/Sidebar'

function Processos() {
  const [lista, setLista] = useState([])
  const [loading, setLoading] = useState(true)
  
  // MODAL DE NOVO PROCESSO
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [clientes, setClientes] = useState([])
  const [novoProcesso, setNovoProcesso] = useState({
    numero: '', cliente: '', contra_parte: '', tipo_acao: 'Cível', data_prazo: ''
  })
  const [extracting, setExtracting] = useState(false) 
  const hiddenFileInput = useRef(null) 

  // DRAWER DA IA
  const { isOpen: isIAOpen, onOpen: onIAOpen, onClose: onIAClose } = useDisclosure()
  const [processoSelecionado, setProcessoSelecionado] = useState(null)
  
  // ESTADOS DA IA (RESUMO E CHAT)
  const [resumoIA, setResumoIA] = useState('')
  const [loadingIA, setLoadingIA] = useState(false)
  const drawerFileInput = useRef(null)

  // ESTADOS DO CHAT
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState([]) // Lista de mensagens
  const [sendingChat, setSendingChat] = useState(false)
  const chatEndRef = useRef(null) // Para rolar a tela pra baixo

  const toast = useToast()
  const [saving, setSaving] = useState(false)

  // 1. CARREGAR DADOS
  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }
      const resProc = await axios.get('http://127.0.0.1:8000/processos', { headers })
      setLista(resProc.data)
      const resCli = await axios.get('http://127.0.0.1:8000/clientes', { headers })
      setClientes(resCli.data)
    } catch (error) {
      console.log(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  // EFEITO PARA ROLAR O CHAT PARA O FINAL
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [chatMessages])

  // 2. EXTRAIR DADOS DO PDF
  const handleExtractFromPDF = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setExtracting(true)
    const formData = new FormData()
    formData.append('arquivo', file)

    try {
        const response = await axios.post('http://127.0.0.1:8000/ia/extrair-dados', formData)
        const dados = response.data

        setNovoProcesso({
            ...novoProcesso,
            numero: dados.numero_processo || '',
            cliente: dados.cliente || '', 
            contra_parte: dados.contra_parte || '',
            data_prazo: dados.data_prazo || ''
        })
        toast({ title: 'Dados extraídos!', status: 'success' })
    } catch (error) {
        toast({ title: 'Erro na leitura', status: 'error' })
    } finally {
        setExtracting(false)
        event.target.value = null
    }
  }

  // 3. SALVAR
  const handleSave = async () => {
    setSaving(true)
    try {
        const token = localStorage.getItem('token')
        const payload = { ...novoProcesso, status: 'Em Andamento' }
        await axios.post('http://127.0.0.1:8000/processos', payload, {
            headers: { Authorization: `Bearer ${token}` }
        })
        toast({ title: 'Processo criado!', status: 'success' })
        setNovoProcesso({ numero: '', cliente: '', contra_parte: '', tipo_acao: 'Cível', data_prazo: '' })
        onClose()
        fetchData()
    } catch (error) {
        toast({ title: 'Erro ao salvar', status: 'error' })
    } finally {
        setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if(!window.confirm("Excluir?")) return;
    try {
        const token = localStorage.getItem('token')
        await axios.delete(`http://127.0.0.1:8000/processos/${id}`, { headers: { Authorization: `Bearer ${token}` } })
        fetchData()
        toast({ title: 'Excluído', status: 'success' })
    } catch (error) { toast({ title: 'Erro', status: 'error' }) }
  }

  // --- FUNÇÕES DA IA (DRAWER) ---
  const abrirIA = (proc) => {
    setProcessoSelecionado(proc)
    setResumoIA(proc.resumo_ia || '')
    // Reseta o chat quando abre um processo novo
    setChatMessages([
        { role: 'assistant', text: 'Olá! Sou a IA jurídica. Faça uma pergunta sobre este processo.' }
    ])
    onIAOpen()
  }

  const handleUploadPDFDrawer = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('arquivo', file)
    try {
        const token = localStorage.getItem('token')
        await axios.post(`http://127.0.0.1:8000/processos/${processoSelecionado.id}/anexo`, formData, {
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' }
        })
        toast({ title: 'PDF Enviado!', status: 'success' })
        setProcessoSelecionado({...processoSelecionado, arquivo_pdf: 'sim'})
        fetchData()
    } catch (error) { toast({ title: 'Erro no upload', status: 'error' }) }
  }

  const handleGerarResumo = async () => {
    setLoadingIA(true)
    try {
        const token = localStorage.getItem('token')
        const response = await axios.post(`http://127.0.0.1:8000/processos/${processoSelecionado.id}/analise-ia`, {}, {
            headers: { Authorization: `Bearer ${token}` }
        })
        setResumoIA(response.data.resumo)
        fetchData()
    } catch (error) { toast({ title: 'Erro na IA', status: 'error' }) } finally { setLoadingIA(false) }
  }

  // --- FUNÇÃO NOVA: ENVIAR MENSAGEM NO CHAT ---
  const handleEnviarChat = async () => {
    if (!chatInput.trim()) return

    // 1. Adiciona a mensagem do usuário na tela
    const novaMensagemUsuario = { role: 'user', text: chatInput }
    setChatMessages((prev) => [...prev, novaMensagemUsuario])
    setChatInput('') // Limpa campo
    setSendingChat(true)

    try {
        const token = localStorage.getItem('token')
        // 2. Manda pro Python
        const response = await axios.post(`http://127.0.0.1:8000/processos/${processoSelecionado.id}/chat`, 
            { pergunta: novaMensagemUsuario.text }, 
            { headers: { Authorization: `Bearer ${token}` } }
        )

        // 3. Adiciona a resposta da IA na tela
        const novaMensagemIA = { role: 'assistant', text: response.data.resposta }
        setChatMessages((prev) => [...prev, novaMensagemIA])

    } catch (error) {
        toast({ title: 'Erro no chat', status: 'error' })
        setChatMessages((prev) => [...prev, { role: 'assistant', text: 'Desculpe, tive um erro ao ler o processo.' }])
    } finally {
        setSendingChat(false)
    }
  }

  return (
    <Box bg="gray.50" minH="100vh">
      <Sidebar />
      <Box ml="250px" p={8}>
        <Container maxW="container.xl">
          <Flex justify="space-between" align="center" mb={6}>
            <Heading size="lg" color="gray.700">📂 Meus Processos</Heading>
            <Button leftIcon={<FiPlus />} colorScheme="blue" onClick={onOpen}>Novo Processo</Button>
          </Flex>

          <Box bg="white" borderRadius="lg" shadow="sm" overflow="hidden">
            <Table variant="simple">
              <Thead bg="gray.50">
                <Tr><Th>Número</Th><Th>Cliente</Th><Th>Status</Th><Th>IA & Ações</Th></Tr>
              </Thead>
              <Tbody>
                {lista.map((proc) => (
                    <Tr key={proc.id}>
                      <Td fontWeight="bold">{proc.numero}</Td>
                      <Td>{proc.cliente}</Td>
                      <Td><Badge colorScheme="blue">{proc.status}</Badge></Td>
                      <Td>
                        <Flex gap={2}>
                            <Button size="sm" leftIcon={<FiCpu />} colorScheme="purple" variant={proc.resumo_ia ? "solid" : "outline"} onClick={() => abrirIA(proc)}>
                                {proc.resumo_ia ? "Ver Análise" : "Analisar"}
                            </Button>
                            <IconButton icon={<FiTrash2 />} size="sm" colorScheme="red" variant="ghost" onClick={() => handleDelete(proc.id)}/>
                        </Flex>
                      </Td>
                    </Tr>
                  ))}
              </Tbody>
            </Table>
          </Box>

          {/* MODAL NOVO PROCESSO */}
          <Modal isOpen={isOpen} onClose={onClose} size="xl">
            <ModalOverlay />
            <ModalContent>
              <ModalHeader>Novo Processo</ModalHeader>
              <ModalCloseButton />
              <ModalBody>
                <Box mb={6} p={4} bg="purple.50" borderRadius="md" border="1px dashed" borderColor="purple.300">
                    <input type="file" accept="application/pdf" style={{ display: 'none' }} ref={hiddenFileInput} onChange={handleExtractFromPDF} />
                    <Flex align="center" justify="space-between">
                        <VStack align="start" spacing={0}>
                            <Text fontWeight="bold" color="purple.700">Tem o PDF da Inicial?</Text>
                            <Text fontSize="sm" color="purple.600">A IA lê e preenche os campos.</Text>
                        </VStack>
                        <Button leftIcon={<FiZap />} colorScheme="purple" size="sm" onClick={() => hiddenFileInput.current.click()} isLoading={extracting} loadingText="Lendo...">
                            Preencher com IA
                        </Button>
                    </Flex>
                </Box>
                <VStack spacing={4}>
                    <Input placeholder="Número" value={novoProcesso.numero} onChange={(e) => setNovoProcesso({...novoProcesso, numero: e.target.value})} />
                    <Select placeholder="Cliente" value={novoProcesso.cliente} onChange={(e) => setNovoProcesso({...novoProcesso, cliente: e.target.value})}>
                        {clientes.map(cli => <option key={cli.id} value={cli.nome}>{cli.nome}</option>)}
                    </Select>
                    <Input placeholder="Réu" value={novoProcesso.contra_parte} onChange={(e) => setNovoProcesso({...novoProcesso, contra_parte: e.target.value})} />
                    <Input type="date" value={novoProcesso.data_prazo} onChange={(e) => setNovoProcesso({...novoProcesso, data_prazo: e.target.value})} />
                </VStack>
              </ModalBody>
              <ModalFooter>
                <Button mr={3} onClick={onClose}>Cancelar</Button>
                <Button colorScheme="blue" onClick={handleSave} isLoading={saving}>Salvar</Button>
              </ModalFooter>
            </ModalContent>
          </Modal>

          {/* --- DRAWER (PAINEL LATERAL) COM ABAS --- */}
          <Drawer isOpen={isIAOpen} placement="right" onClose={onIAClose} size="md">
            <DrawerOverlay />
            <DrawerContent>
              <DrawerCloseButton />
              <DrawerHeader borderBottomWidth="1px">🤖 Inteligência Artificial</DrawerHeader>
              
              <DrawerBody p={0}>
                <Tabs isFitted variant="enclosed" colorScheme="purple" h="full" display="flex" flexDirection="column">
                    <TabList mb={0}>
                        <Tab>📄 Resumo</Tab>
                        <Tab>💬 Chat com PDF</Tab>
                    </TabList>

                    <TabPanels flex="1" overflowY="auto">
                        
                        {/* ABA 1: RESUMO (Igual antes) */}
                        <TabPanel>
                            <VStack spacing={6} align="stretch" mt={4}>
                                <Box border="1px dashed" borderColor="gray.300" p={6} borderRadius="md" textAlign="center" bg="gray.50">
                                    <input type="file" accept="application/pdf" style={{ display: 'none' }} ref={drawerFileInput} onChange={handleUploadPDFDrawer} />
                                    <VStack>
                                        <FiFileText size={30} color="gray" />
                                        {processoSelecionado?.arquivo_pdf ? <Text color="green.600" fontWeight="bold">PDF Anexado ✅</Text> : <Text color="gray.500">Sem PDF</Text>}
                                        <Button size="sm" leftIcon={<FiUpload />} onClick={() => drawerFileInput.current.click()}>Enviar/Trocar PDF</Button>
                                    </VStack>
                                </Box>
                                <Button colorScheme="purple" leftIcon={<FiCpu />} onClick={handleGerarResumo} isLoading={loadingIA} isDisabled={!processoSelecionado?.arquivo_pdf}>
                                    Gerar Resumo Completo
                                </Button>
                                {resumoIA && (
                                    <Box bg="purple.50" p={4} borderRadius="md" border="1px" borderColor="purple.100">
                                        <Box className="markdown-body" fontSize="sm" color="gray.800" sx={{ 'ul': { paddingLeft: '20px' }, 'strong': { color: 'purple.900' } }}>
                                            <ReactMarkdown>{resumoIA}</ReactMarkdown>
                                        </Box>
                                    </Box>
                                )}
                            </VStack>
                        </TabPanel>

                        {/* ABA 2: CHAT (NOVIDADE) */}
                        <TabPanel display="flex" flexDirection="column" h="calc(100vh - 150px)" p={0}>
                            {/* LISTA DE MENSAGENS */}
                            <Box flex="1" overflowY="auto" p={4} bg="gray.50">
                                {chatMessages.map((msg, idx) => (
                                    <Flex key={idx} justify={msg.role === 'user' ? 'flex-end' : 'flex-start'} mb={3}>
                                        {msg.role === 'assistant' && <Avatar size="xs" src="https://bit.ly/broken-link" icon={<FiCpu />} bg="purple.500" mr={2} />}
                                        <Box 
                                            bg={msg.role === 'user' ? 'blue.500' : 'white'} 
                                            color={msg.role === 'user' ? 'white' : 'gray.800'}
                                            p={3} 
                                            borderRadius="lg" 
                                            shadow="sm"
                                            maxW="80%"
                                        >
                                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                                        </Box>
                                    </Flex>
                                ))}
                                {sendingChat && (
                                    <Flex justify="flex-start" mb={3}>
                                        <Avatar size="xs" bg="purple.500" icon={<FiCpu />} mr={2} />
                                        <Box bg="white" p={3} borderRadius="lg" shadow="sm">
                                            <Spinner size="xs" /> Digitando...
                                        </Box>
                                    </Flex>
                                )}
                                <div ref={chatEndRef} />
                            </Box>

                            {/* CAMPO DE DIGITAÇÃO */}
                            <Box p={3} bg="white" borderTop="1px" borderColor="gray.200">
                                <HStack>
                                    <Input 
                                        placeholder="Pergunte sobre o processo..." 
                                        value={chatInput} 
                                        onChange={(e) => setChatInput(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleEnviarChat()}
                                        isDisabled={!processoSelecionado?.arquivo_pdf} // Trava se não tiver PDF
                                    />
                                    <IconButton 
                                        colorScheme="blue" 
                                        icon={<FiSend />} 
                                        onClick={handleEnviarChat} 
                                        isLoading={sendingChat}
                                        isDisabled={!processoSelecionado?.arquivo_pdf}
                                    />
                                </HStack>
                                {!processoSelecionado?.arquivo_pdf && (
                                    <Text fontSize="xs" color="red.400" mt={1}>Anexe um PDF na aba Resumo primeiro.</Text>
                                )}
                            </Box>
                        </TabPanel>

                    </TabPanels>
                </Tabs>
              </DrawerBody>
            </DrawerContent>
          </Drawer>

        </Container>
      </Box>
    </Box>
  )
}

export default Processos