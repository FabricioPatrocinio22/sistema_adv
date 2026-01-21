import { useEffect, useState } from 'react'
import { 
  Box, Heading, Table, Thead, Tbody, Tr, Th, Td, Button, Flex, 
  IconButton, useToast, Skeleton, Text, Container,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalFooter, ModalBody, ModalCloseButton,
  FormControl, FormLabel, Input, useDisclosure, VStack 
} from '@chakra-ui/react'
import { FiPlus, FiTrash2, FiUser } from 'react-icons/fi'
import axios from 'axios'
import Sidebar from './components/Sidebar'
import { maskDocumento, maskTelefone } from './utils/masks'

function Clientes() {
  const [lista, setLista] = useState([])
  const [loading, setLoading] = useState(true)
  
  // ESTADOS DO MODAL
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [saving, setSaving] = useState(false)
  
  // DADOS DO NOVO CLIENTE
  const [novoCliente, setNovoCliente] = useState({
    nome: '',
    cpf_cnpj: '',
    email: '',
    telefone: ''
  })

  const toast = useToast()

  // 1. BUSCAR CLIENTES
  const fetchClientes = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/clientes`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setLista(response.data)
    } catch (error) {
      toast({ title: 'Erro ao buscar clientes', status: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchClientes()
  }, [])

  // 2. SALVAR NOVO CLIENTE
  const handleSave = async () => {
    if (!novoCliente.nome || !novoCliente.cpf_cnpj) {
        toast({ title: 'Nome e Documento são obrigatórios', status: 'warning' })
        return
    }

    setSaving(true)
    try {
        const token = localStorage.getItem('token')
        await axios.post(`${import.meta.env.VITE_API_URL}/clientes`, novoCliente, {
            headers: { Authorization: `Bearer ${token}` }
        })

        toast({ title: 'Cliente cadastrado!', status: 'success' })
        
        setNovoCliente({ nome: '', cpf_cnpj: '', email: '', telefone: '' }) // Limpa formulário
        onClose() // Fecha modal
        fetchClientes() // Atualiza tabela

    } catch (error) {
        const msg = error.response?.data?.detail || "Erro ao salvar"
        toast({ title: 'Erro', description: msg, status: 'error' })
    } finally {
        setSaving(false)
    }
  }

  // 3. DELETAR CLIENTE
  const handleDelete = async (id) => {
    if(!window.confirm("Excluir este cliente?")) return;
    try {
        const token = localStorage.getItem('token')
        await axios.delete(`${import.meta.env.VITE_API_URL}/clientes/${id}`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        toast({ title: 'Cliente removido', status: 'success' })
        fetchClientes()
    } catch (error) {
        toast({ title: 'Erro ao excluir', status: 'error' })
    }
  }

  return (
    <Box bg="gray.50" minH="100vh">
      <Sidebar />

      <Box ml="250px" p={8}>
        <Container maxW="container.xl">
            
          <Flex justify="space-between" align="center" mb={6}>
            <Heading size="lg" color="gray.700">👥 Carteira de Clientes</Heading>
            <Button leftIcon={<FiPlus />} colorScheme="blue" onClick={onOpen}>
              Novo Cliente
            </Button>
          </Flex>

          <Box bg="white" borderRadius="lg" shadow="sm" overflow="hidden">
            <Table variant="simple">
              <Thead bg="gray.50">
                <Tr>
                  <Th>Nome</Th>
                  <Th>Documento (CPF/CNPJ)</Th>
                  <Th>Contato</Th>
                  <Th>Ações</Th>
                </Tr>
              </Thead>
              <Tbody>
                {loading ? (
                   [1,2,3].map(i => <Tr key={i}><Td colSpan={4}><Skeleton height="20px" /></Td></Tr>)
                ) : lista.length === 0 ? (
                    <Tr><Td colSpan={4} textAlign="center" py={10} color="gray.500">Nenhum cliente cadastrado.</Td></Tr>
                ) : (
                    lista.map((cli) => (
                    <Tr key={cli.id}>
                      <Td fontWeight="bold">
                        <Flex align="center" gap={2}>
                            <FiUser color="gray" /> {cli.nome}
                        </Flex>
                      </Td>
                      <Td>{cli.cpf_cnpj}</Td>
                      <Td>
                        <Text fontSize="sm">{cli.email}</Text>
                        <Text fontSize="xs" color="gray.500">{cli.telefone}</Text>
                      </Td>
                      <Td>
                        <IconButton 
                            icon={<FiTrash2 />} 
                            size="sm" 
                            colorScheme="red" 
                            variant="ghost" 
                            onClick={() => handleDelete(cli.id)}
                        />
                      </Td>
                    </Tr>
                  ))
                )}
              </Tbody>
            </Table>
          </Box>

          {/* --- MODAL DE CADASTRO --- */}
          <Modal isOpen={isOpen} onClose={onClose}>
            <ModalOverlay />
            <ModalContent>
              <ModalHeader>Novo Cliente</ModalHeader>
              <ModalCloseButton />
              
              <ModalBody>
                <VStack spacing={4}>
                    <FormControl isRequired>
                        <FormLabel>Nome Completo</FormLabel>
                        <Input 
                            value={novoCliente.nome}
                            onChange={(e) => setNovoCliente({...novoCliente, nome: e.target.value})}
                        />
                    </FormControl>

                    <FormControl isRequired>
                        <FormLabel>CPF ou CNPJ (Só números)</FormLabel>
                        <Input 
                            value={novoCliente.cpf_cnpj}
                            onChange={(e) => {
                                // AQUI ESTÁ O TRUQUE:
                                const valorFormatado = maskDocumento(e.target.value)
                                setNovoCliente({...novoCliente, cpf_cnpj: valorFormatado})
                            }}
                            placeholder="000.000.000-00"
                            maxLength={18} // Impede digitar mais que um CNPJ formatado
                        />
                    </FormControl>

                    <FormControl>
                        <FormLabel>E-mail</FormLabel>
                        <Input 
                            value={novoCliente.email}
                            onChange={(e) => setNovoCliente({...novoCliente, email: e.target.value})}
                        />
                    </FormControl>

                    <FormControl>
                        <FormLabel>Telefone</FormLabel>
                        <Input 
                            value={novoCliente.telefone}
                            onChange={(e) => {
                                const valorFormatado = maskTelefone(e.target.value)
                                setNovoCliente({...novoCliente, telefone: valorFormatado})
                            }}
                            placeholder="(00) 90000-0000"
                            maxLength={15}
                        />
                </FormControl>
                </VStack>
              </ModalBody>

              <ModalFooter>
                <Button variant="ghost" mr={3} onClick={onClose}>Cancelar</Button>
                <Button colorScheme="blue" onClick={handleSave} isLoading={saving}>
                  Salvar Cliente
                </Button>
              </ModalFooter>
            </ModalContent>
          </Modal>

        </Container>
      </Box>
    </Box>
  )
}

export default Clientes