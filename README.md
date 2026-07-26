# Processo Seletivo – Intensivo Maker | IoT

## Identificação do Candidato

- **Nome Completo:** Gabrielle Cordeiro Santana
- **GitHub:** https://github.com/HelloHinnie

---

## Visão Geral da Solução

O projeto consiste no desenvolvimento de um Sistema de Monitoramento de Temperatura e Abertura de Porta voltado para ambientes de controle crítico, como Smart Coolers, estufas e painéis elétricos. A sua função principal é monitorar caso a porta fique aberta muito tempo, além de aumento da temperatura durante este momento, que levaria a degradação térmica. Além disso, o sistema monitora caso a porta seja fechadda e a temperatura anterior seja retomada. O usuário interage com o sistema por meio da abertura e do fechamento da porta através de um botão, ação que dita a mudança de estado e a consequente normalização do monitoramento, enquanto o firmware aciona alertas automáticos sempre que os limites de tolerância e segurança são violados.

---

## Arquitetura do Sistema Embarcado

O início do código contém uma parte sintetizada da biblioteca do MPU6050, utilizando somente sua função de leitura de temperatura.
O programa foi modularizado em quatro funções:

- inicializar_sistema(): Lê a temperatura inicial assim que o sistema liga para registrar na variável global temp_referencia e garantir uma linha de base, além de imprimir a mensagem obrigatória de inicialização do monitoramento.
```python
def inicializar_sistema():
    global temp_referencia
    try:
        temp_referencia = imu1.read_temperature()
    except:
        pass
    print("Sistema de Monitoramento Inicializado")
```
- verificar_porta(): É a responsável por analisar o estado de abertura da porta. Guarda o momento em que a porta foi aberta na variável tempo_inicio com time.ticks_ms(), que retorna o instante atual de execução do programa em milissegundos. Posteriormente, subtrai o tempo atual do tempo de abertura e verifica se ultrapassou o limite parametrizado constante LIMITE_TEMPO_X, alterando o estado da variável alarme_porta_disparado para evitar a impressão contínua do alerta.
```python
def verificar_porta(estado_botao):
    global porta_aberta, tempo_inicio, alarme_porta_disparado, em_alerta
    
    if estado_botao == 0 and not porta_aberta:
        porta_aberta = True
        tempo_inicio = time.ticks_ms() 
    elif estado_botao == 1 and porta_aberta:
        porta_aberta = False
        
    if porta_aberta and not alarme_porta_disparado:
        if time.ticks_diff(time.ticks_ms(), tempo_inicio) >= LIMITE_TEMPO_X:
            print("ALERTA: Porta aberta por muito tempo!")
            alarme_porta_disparado = True 
            em_alerta = True
```
- verificar_temperatura(): Lê a leitura atual do IMU (temp_atual) e calcula o delta_t em relação à temp_referencia. Caso o gradiente térmico seja maior ou igual ao LIMITE_VARIACAO_Y, ele dispara o alerta térmico. A variável de referência só é atualizada por uma nova temperatura se a porta estiver fechada (estado_botao == 1) e se a temperatura recuar para um valor mais baixo.

```python
def verificar_temperatura(estado_botao, temp_atual):
    global temp_referencia, alarme_termico_disparado, em_alerta

    if estado_botao == 1 and temp_atual < temp_referencia:
        temp_referencia = temp_atual
        
    delta_t = temp_atual - temp_referencia
    
    if delta_t >= LIMITE_VARIACAO_Y and not alarme_termico_disparado:
        print("ALERTA: Degradacao termica detectada!")
        alarme_termico_disparado = True
        em_alerta = True
```
- verificar_normalizacao(): Verifica primeiramente se o sistema estava em_alerta e avalia se as condições seguras foram restauradas simultaneamente (botão retornou ao estado 1 e delta_t recuou para menos que o limite). Caso positivo, ele aplica um atraso intencional de 700ms (time.sleep_ms(700)) para fins de sincronização na esteira CI/CD e reinicia os estados das flags para False.
```python
def verificar_normalizacao(estado_botao, temp_atual):
    global alarme_porta_disparado, alarme_termico_disparado, em_alerta
    
    if em_alerta:
        delta_t = temp_atual - temp_referencia
        
        # Só normaliza se a porta fechou E a temperatura baixou
        if estado_botao == 1 and delta_t < LIMITE_VARIACAO_Y:
            time.sleep_ms(700) 
            print("Status: Sistema Normalizado.")
            alarme_porta_disparado = False
            alarme_termico_disparado = False
            em_alerta = False
```
Todas essas funções são chamadas dentro do loop principal.
```python
# Executa a inicialização
inicializar_sistema()

# Loop Principal
while True:
    estado_botao_atual = btn1.value()
    
    try:
        temp_atual_leitura = imu1.read_temperature()
    except:
        temp_atual_leitura = temp_referencia
        
    verificar_porta(estado_botao_atual)
    verificar_temperatura(estado_botao_atual, temp_atual_leitura)
    verificar_normalizacao(estado_botao_atual, temp_atual_leitura)
    
    time.sleep(0.1)
```

---

## Componentes Utilizados na Simulação

- Placa ESP32 DevKitC V4: Microcontrolador responsável pela lógica do sistema e comunicação entre dispositivos.
- Sensor de Temperatura MPU6050: Lê a temperatura do ambiente.
- Botão: Representa a abertura e fechamento da porta.

<img width="415" height="313" alt="image" src="https://github.com/user-attachments/assets/60dec8c7-454b-4484-b4f3-e65ebb10bdbc" />

---

## Decisões Técnicas Relevantes

- Tive dificuldades para passar a biblioteca do MPU6050 na verificação, por algum motivo não importava como eu colocasse, não conseguia identificar a biblioteca, o que me levou a colocar ela simplificada no próprio main.py.
- Inicialmente fiz a programação toda no loop principal, mas conforme o código foi ficando mais complexo, decidi que era melhor separar em funções para serem chamadas no laço central, por questão de organização.
- Os valores de calibração foram salvas como contantes no cabeçalho do arquivo, e as variáveis globais agem como uma máquina de estados, guardando os estados anteriores.
---

## Resultados Obtidos

O sistema funciona conforme o esperado na simulação do Wokwi, ativando o alarme no terminal quando a porta fica aberta por um período contínuo além do limite tolerado, ou quando há um aumento repentino na leitura de temperatura do ambiente, além de imprimir a mensagem de sistema normalizado após as condições de risco terem subsidiado. Desse modo, o resultado saiu como esperado e atendendo os requisitos solicitados.

---

