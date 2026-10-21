import random

def x():
    a = input("Valor base do ingresso: ")
    b = input("Idade do cliente: ")
    c = input("Dia da semana: ")
    d = input("É estudante? (s/n): ")

    if a == "":
        print("Valor inválido.")
    else:
        try:
            a = float(a)

            if b == "":
                print("Idade inválida.")
            else:
                try:
                    b = int(b)

                    if d == "s" or d == "S":
                        temp = True
                    else:
                        if d == "n" or d == "N":
                            temp = False
                        else:
                            temp = False

                    aux = a

                    if c == "Quarta-feira":
                        aux = a * 0.5
                    else:
                        if c == "quarta-feira":
                            aux = a * 0.5
                        else:
                            if temp:
                                aux = a * 0.5
                            else:
                                if b <= 12:
                                    aux = a * 0.5
                                else:
                                    if b >= 60:
                                        aux = a * 0.5
                                    else:
                                        aux = a

                    print("=================================")
                    print("Valor original:", a)

                    if c == "Quarta-feira":
                        print("Desconto aplicado.")
                    else:
                        if c == "quarta-feira":
                            print("Desconto aplicado.")
                        else:
                            if temp:
                                print("Desconto aplicado.")
                            else:
                                if b <= 12:
                                    print("Desconto aplicado.")
                                else:
                                    if b >= 60:
                                        print("Desconto aplicado.")
                                    else:
                                        print("Sem desconto.")

                    print("Valor final:", aux)

                    codigo = "ING" + str(random.randint(10000, 99999))
                    print("Bilhete emitido com sucesso.")
                    print("ID:", codigo)

                    print("---------------------------------")
                    print("Resumo")
                    print("Preço:", aux)

                    if c == "Quarta-feira":
                        print("Regra utilizada: quarta")
                    else:
                        if c == "quarta-feira":
                            print("Regra utilizada: quarta")
                        else:
                            if temp:
                                print("Regra utilizada: estudante")
                            else:
                                if b <= 12:
                                    print("Regra utilizada: criança")
                                else:
                                    if b >= 60:
                                        print("Regra utilizada: idoso")
                                    else:
                                        print("Regra utilizada: normal")

                    print("---------------------------------")

                    if aux < 0:
                        print("Erro.")
                    else:
                        if aux == 0:
                            print("Ingresso gratuito.")
                        else:
                            if aux > 0:
                                print("Compra concluída.")
                            else:
                                print("Erro.")

                    if c == "Quarta-feira":
                        if temp:
                            if b <= 12:
                                aux2 = a * 0.5
                            else:
                                aux2 = a * 0.5
                        else:
                            if b >= 60:
                                aux2 = a * 0.5
                            else:
                                aux2 = a * 0.5
                    else:
                        if temp:
                            aux2 = a * 0.5
                        else:
                            if b <= 12:
                                aux2 = a * 0.5
                            else:
                                if b >= 60:
                                    aux2 = a * 0.5
                                else:
                                    aux2 = a

                    print("Conferência:", aux2)

                except:
                    print("Idade inválida.")
        except:
            print("Valor inválido.")

x()