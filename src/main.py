import machine
import time
#Biblioteca do MPU6050
import mpu6050

#Constantes
LIMITE_TEMPO_X = 5000      
LIMITE_VARIACAO_Y = 3.0    

#Variáveis de Estado
porta_aberta = False
tempo_inicio = 0
temp_referencia = 0.0


alarme_porta_disparado = False 
alarme_termico_disparado = False
em_alerta = False 

#Inicialização do hardware, uma instância do MPU6050 denominada 'imu1' e um botão
#O PULL_DOWN força a leitura 0 quando solto. Quando o botão  é pressionado, o 3V3 chega e ele lê 1.
btn1 = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_DOWN)
imu1 = mpu6050.MPU6050()

#Inicializa o sistema, lendo uma temperatura inicial para ser mais preciso
def inicializar_sistema():
    global temp_referencia
    try:
        temp_referencia = imu1.read_temperature()
    except:
        pass
    print("Sistema de Monitoramento Inicializado")

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

def verificar_temperatura(estado_botao, temp_atual):
    global temp_referencia, alarme_termico_disparado, em_alerta
    
    if estado_botao == 1 and not alarme_termico_disparado:
        temp_referencia = temp_atual
        
    delta_t = temp_atual - temp_referencia
    
    if delta_t >= LIMITE_VARIACAO_Y and not alarme_termico_disparado:
        print("ALERTA: Degradacao termica detectada!")
        alarme_termico_disparado = True
        em_alerta = True

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


inicializar_sistema()

#Verifica a cada iteração
while True:
    #Captura o estado atual dos sensores apenas uma vez por ciclo
    estado_botao_atual = btn1.value()
    
    try:
        temp_atual_leitura = imu1.read_temperature()
    except:
        temp_atual_leitura = temp_referencia
        
    # 2. Distribui os dados coletados para a máquina de estados
    verificar_porta(estado_botao_atual)
    verificar_temperatura(estado_botao_atual, temp_atual_leitura)
    verificar_normalizacao(estado_botao_atual, temp_atual_leitura)
    
    time.sleep(0.1)