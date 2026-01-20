import { useEffect, useState } from 'react'
import { 
  Box, Heading, Table, Thead, Tbody, Tr, Th, Td, Badge, Button, Flex, 
  IconButton, useToast, Skeleton, Text, Container,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalFooter, ModalBody, ModalCloseButton,
  FormControl, FormLabel, Input, Select, useDisclosure, VStack, HStack, Stat, StatLabel, StatNumber, StatArrow 
} from '@chakra-ui/react'
import { FiPlus, FiTrash2, FiTrendingUp, FiTrendingDown } from 'react-icons/fi'
import axios from 'axios'
import Sidebar from './components/Sidebar'
import { maskMoeda } from './utils/masks' // <--- Importando nossa máscara

function Financeiro() {
  const [lista, setLista] = useState([])
  const [loading, setLoading] = useState(true)
  
  // Resumo rápido no topo da tela
  const [resumo, setResumo] = useState({ entradas: 0, saidas: 0, saldo: 0 })

  const { isOpen, onOpen, onClose } = useDisclosure()
  const [saving, setSaving] = useState(false)
  const toast = useToast()

  // FORMULÁRIO
  const [novoLancamento, setNovoLancamento] = useState({
    descricao: '',
    tipo: 'Entrada', // ou 'Saida'
    valor: '', // Vai ser string formatada (R$ 100,00)
    data_pagamento: '',
    status: 'Pendente' // ou 'Pago'
  })

  // 1. BUSCAR DADOS
  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }
      
      // Vamos assumir que existe essa rota no Python (se não tiver, criamos já já)
      const response = await axios.get('${import.meta.env.VITE_API_URL}/pagamentos', { headers })
      
      setLista(response.data)
      calcularResumo(response.data)

    } catch (error) {
      // Se der 404 é porque ainda não criamos a rota no Python, tudo bem por enquanto
      console.log("Rota ainda não criada ou erro de conexão")
    } finally {
      setLoading(false)
    }
  }

  // Função auxiliar para calcular totais localmente (Frontend Power)
  const calcularResumo = (dados) => {
    let ent = 0
    let sai = 0
    dados.forEach(item => {
        if (item.tipo === 'Entrada') ent += Number(item.valor)
        else sai += Number(item.valor)
    })
    setResumo({ entradas: ent, saidas: sai, saldo: ent - sai })
  }

  useEffect(() => {
    fetchData()
  }, [])

  // 2. SALVAR LANÇAMENTO
  const handleSave = async () => {
    if (!novoLancamento.descricao || !novoLancamento.valor) {
        toast({ title: 'Preencha a descrição e o valor', status: 'warning' })
        return
    }

    setSaving(true)
    try {
        const token = localStorage.getItem('token')
        
        // TRUQUE DO DINHEIRO: 
        // O Python espera um número (float e.g. 1500.50), mas o input está "R$ 1.500,50"
        // Precisamos limpar a sujeira antes de enviar.
        const valorLimpo = novoLancamento.valor
            .replace("R$", "")      // Tira o símbolo
            .replace(/\./g, "")     // Tira os pontos de milhar
            .replace(",", ".")      // Troca vírgula por ponto
            .trim()                 // Tira espaços

        const payload = {
            ...novoLancamento,
            valor: parseFloat(valorLimpo) // Converte pra número
        }

        await axios.post('${import.meta.env.VITE_API_URL}/pagamentos', payload, {
            headers: { Authorization: `Bearer ${token}` }
        })

        toast({ title: 'Lançamento salvo!', status: 'success' })
        setNovoLancamento({ descricao: '', tipo: 'Entrada', valor: '', data_pagamento: '', status: 'Pendente' })
        onClose()
        fetchData()

    } catch (error) {
        toast({ title: 'Erro ao salvar', description: "Verifique o Backend", status: 'error' })
    } finally {
        setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if(!window.confirm("Apagar este registro?")) return;
    try {
        const token = localStorage.getItem('token')
        await axios.delete(`${import.meta.env.VITE_API_URL}/pagamentos/${id}`, {
             headers: { Authorization: `Bearer ${token}` }
        })
        fetchData()
        toast({ title: 'Apagado com sucesso', status: 'success' })
    } catch (error) {
        toast({ title: 'Erro ao apagar', status: 'error' })
    }
  }

  return (
    <Box bg="gray.50" minH="100vh">
      <Sidebar />

      <Box ml="250px" p={8}>
        <Container maxW="container.xl">
            
          <Flex justify="space-between" align="center" mb={6}>
            <Heading size="lg" color="gray.700">💰 Fluxo de Caixa</Heading>
            <Button leftIcon={<FiPlus />} colorScheme="green" onClick={onOpen}>
              Novo Lançamento
            </Button>
          </Flex>

          {/* CARDS DE RESUMO NO TOPO */}
          <Flex gap={4} mb={6}>
            <Box p={4} bg="white" shadow="sm" borderRadius="md" flex={1}>
                <Stat>
                    <StatLabel>Entradas (Honorários)</StatLabel>
                    <StatNumber color="green.500">
                        <StatArrow type="increase" /> R$ {resumo.entradas.toFixed(2)}
                    </StatNumber>
                </Stat>
            </Box>
            <Box p={4} bg="white" shadow="sm" borderRadius="md" flex={1}>
                <Stat>
                    <StatLabel>Saídas (Despesas)</StatLabel>
                    <StatNumber color="red.500">
                        <StatArrow type="decrease" /> R$ {resumo.saidas.toFixed(2)}
                    </StatNumber>
                </Stat>
            </Box>
            <Box p={4} bg="blue.600" color="white" shadow="sm" borderRadius="md" flex={1}>
                <Stat>
                    <StatLabel color="blue.100">Saldo Atual</StatLabel>
                    <StatNumber>R$ {resumo.saldo.toFixed(2)}</StatNumber>
                </Stat>
            </Box>
          </Flex>

          {/* TABELA */}
          <Box bg="white" borderRadius="lg" shadow="sm" overflow="hidden">
            <Table variant="simple">
              <Thead bg="gray.50">
                <Tr>
                  <Th>Descrição</Th>
                  <Th>Tipo</Th>
                  <Th>Valor</Th>
                  <Th>Status</Th>
                  <Th>Ações</Th>
                </Tr>
              </Thead>
              <Tbody>
                {loading ? (
                   [1,2,3].map(i => <Tr key={i}><Td colSpan={5}><Skeleton height="20px" /></Td></Tr>)
                ) : lista.length === 0 ? (
                    <Tr><Td colSpan={5} textAlign="center" py={10} color="gray.500">Nenhum lançamento.</Td></Tr>
                ) : (
                    lista.map((item) => (
                    <Tr key={item.id}>
                      <Td fontWeight="bold">{item.descricao}</Td>
                      <Td>
                        <Badge colorScheme={item.tipo === 'Entrada' ? 'green' : 'red'}>
                            {item.tipo}
                        </Badge>
                      </Td>
                      <Td fontWeight="bold" color={item.tipo === 'Entrada' ? 'green.600' : 'red.600'}>
                        {item.tipo === 'Saida' ? '- ' : ''} 
                        {Number(item.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                      </Td>
                      <Td>
                        <Badge variant="outline" colorScheme={item.status === 'Pago' ? 'green' : 'orange'}>
                            {item.status}
                        </Badge>
                      </Td>
                      <Td>
                        <IconButton icon={<FiTrash2 />} size="sm" colorScheme="red" variant="ghost" onClick={() => handleDelete(item.id)}/>
                      </Td>
                    </Tr>
                  ))
                )}
              </Tbody>
            </Table>
          </Box>

          {/* MODAL */}
          <Modal isOpen={isOpen} onClose={onClose}>
            <ModalOverlay />
            <ModalContent>
              <ModalHeader>Novo Lançamento</ModalHeader>
              <ModalCloseButton />
              
              <ModalBody>
                <VStack spacing={4}>
                    <FormControl isRequired>
                        <FormLabel>Descrição</FormLabel>
                        <Input 
                            placeholder="Ex: Honorários Cliente X"
                            value={novoLancamento.descricao}
                            onChange={(e) => setNovoLancamento({...novoLancamento, descricao: e.target.value})}
                        />
                    </FormControl>

                    <HStack w="full">
                        <FormControl>
                            <FormLabel>Tipo</FormLabel>
                            <Select 
                                value={novoLancamento.tipo}
                                onChange={(e) => setNovoLancamento({...novoLancamento, tipo: e.target.value})}
                            >
                                <option value="Entrada">Entrada 🟢</option>
                                <option value="Saida">Saída 🔴</option>
                            </Select>
                        </FormControl>

                        <FormControl isRequired>
                            <FormLabel>Valor</FormLabel>
                            <Input 
                                placeholder="R$ 0,00"
                                value={novoLancamento.valor}
                                onChange={(e) => {
                                    // AQUI A MÁSCARA ENTRA EM AÇÃO
                                    const valor = maskMoeda(e.target.value)
                                    setNovoLancamento({...novoLancamento, valor: valor})
                                }}
                            />
                        </FormControl>
                    </HStack>

                    <HStack w="full">
                        <FormControl>
                            <FormLabel>Data</FormLabel>
                            <Input 
                                type="date"
                                value={novoLancamento.data_pagamento}
                                onChange={(e) => setNovoLancamento({...novoLancamento, data_pagamento: e.target.value})}
                            />
                        </FormControl>
                        <FormControl>
                            <FormLabel>Status</FormLabel>
                            <Select 
                                value={novoLancamento.status}
                                onChange={(e) => setNovoLancamento({...novoLancamento, status: e.target.value})}
                            >
                                <option value="Pendente">Pendente ⏳</option>
                                <option value="Pago">Pago / Recebido ✅</option>
                            </Select>
                        </FormControl>
                    </HStack>

                </VStack>
              </ModalBody>
              <ModalFooter>
                <Button variant="ghost" mr={3} onClick={onClose}>Cancelar</Button>
                <Button colorScheme="green" onClick={handleSave} isLoading={saving}>
                  Confirmar
                </Button>
              </ModalFooter>
            </ModalContent>
          </Modal>

        </Container>
      </Box>
    </Box>
  )
}

export default Financeiro