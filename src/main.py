import machine
import time
from machine import Pin, SoftI2C
from time import sleep_ms

#Biblioteca do MPU6050 simplificada
i2c_err_str = "ESP32 could not communicate with module at address 0x{:02X}, check wiring"

_PWR_MGMT_1 = 0x6B
_TEMP_OUT0 = 0x41
_MPU6050_ADDRESS = 0x68

def signedIntFromBytes(x, endian="big"):
    y = int.from_bytes(x, endian)
    if (y >= 0x8000):
        return -((65535 - y) + 1)
    else:
        return y


class MPU6050(object):     
    def __init__(self, scl_pin=22, sda_pin=21, addr=_MPU6050_ADDRESS):
        self.addr = addr
        self.i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000)
        
        try:
            self.i2c.writeto_mem(self.addr, _PWR_MGMT_1, bytes([0x00]))
            sleep_ms(5)
        except Exception as e:
            print(i2c_err_str.format(self.addr))
            raise e

    def read_temperature(self):
        try:
            rawData = self.i2c.readfrom_mem(self.addr, _TEMP_OUT0, 2)
            raw_temp = signedIntFromBytes(rawData, "big")
        except:
            print(i2c_err_str.format(self.addr))
            return float("NaN")
        
        actual_temp = (raw_temp / 340.0) + 36.53
        return actual_temp

# Constantes
LIMITE_TEMPO_X = 5000      
LIMITE_VARIACAO_Y = 3.0    

# Variáveis de Estado
porta_aberta = False
tempo_inicio = 0
temp_referencia = 0.0

alarme_porta_disparado = False 
alarme_termico_disparado = False
em_alerta = False 

# Inicialização do hardware
btn1 = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_DOWN)
imu1 = MPU6050()

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

    if estado_botao == 1 and temp_atual < temp_referencia:
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