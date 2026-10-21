import random

def sistema_ingresso(x, y, z, w):
    # x = valor base
    # y = idade
    # z = dia da semana
    # w = estudante (True/False)

    a = 0
    temp = 0
    aux = 0
    msg = ""
    id_bilhete = ""

    if z == "Quarta-feira":
        if y < 0:
            msg = "Idade inválida"
            a = -1
        else:
            if x <= 0:
                msg = "Valor inválido"
                a = -1
            else:
                if w == True:
                    temp = x * 0.5
                    a = temp
                    msg = "Desconto aplicado (quarta + estudante)"
                else:
                    temp = x * 0.5
                    a = temp
                    msg = "Desconto aplicado (quarta-feira)"
    else:
        if z != "Quarta-feira":
            if y < 0:
                msg = "Idade inválida"
                a = -1
            else:
                if x <= 0:
                    msg = "Valor inválido"
                    a = -1
                else:
                    if w == True:
                        aux = x * 0.5
                        a = aux
                        msg = "Desconto aplicado (estudante)"
                    else:
                        if y <= 12:
                            aux = x * 0.5
                            a = aux
                            msg = "Desconto aplicado (criança)"
                        else:
                            if y >= 60:
                                aux = x * 0.5
                                a = aux
                                msg = "Desconto aplicado (idoso)"
                            else:
                                a = x
                                msg = "Sem desconto"
    # duplicação desnecessária de geração de ID
    id_bilhete = "ID" + str(random.randint(1000, 9999)) + str(random.randint(1000, 9999))
    if a != -1:
        print("Preço final:", a)
        print("Mensagem:", msg)
        print("Bilhete:", id_bilhete)
    else:
        print("Erro:", msg)
        print("Bilhete não gerado")

# Exemplo de uso
sistema_ingresso(20, 10, "Quarta-feira", False)
sistema_ingresso(30, 25, "Segunda-feira", True)
sistema_ingresso(25, 70, "Domingo", False)
