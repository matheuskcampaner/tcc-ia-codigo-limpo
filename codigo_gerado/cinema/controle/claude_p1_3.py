import random

def f(v, a, d, e):
    x = 0
    temp = ""
    aux = 0
    r = ""
    id_bilhete = ""
    msg = ""
    flag = 0
    flag2 = 0
    flag3 = 0
    y = None
    z = None
    w = None

    if v == None or v <= 0:
        print("Erro: valor invalido")
        return None
    else:
        if a == None or a < 0:
            print("Erro: idade invalida")
            return None
        else:
            if d == None or d == "":
                print("Erro: dia invalido")
                return None
            else:
                if e == None:
                    e = False

                if d == "Quarta-feira" or d == "quarta-feira" or d == "QUARTA-FEIRA" or d == "Quarta" or d == "quarta":
                    flag = 1
                    temp = "desconto de quarta"
                    if a <= 12:
                        flag2 = 1
                        if e == True:
                            flag3 = 1
                            x = v * 0.5
                            r = "desconto quarta (nao cumulativo com estudante/crianca)"
                        else:
                            x = v * 0.5
                            r = "desconto quarta"
                    else:
                        if a >= 60:
                            flag2 = 1
                            if e == True:
                                flag3 = 1
                                x = v * 0.5
                                r = "desconto quarta (nao cumulativo com estudante/idoso)"
                            else:
                                x = v * 0.5
                                r = "desconto quarta"
                        else:
                            if e == True:
                                flag3 = 1
                                x = v * 0.5
                                r = "desconto quarta (nao cumulativo com estudante)"
                            else:
                                x = v * 0.5
                                r = "desconto quarta padrao"
                else:
                    if d == "Segunda-feira" or d == "segunda-feira" or d == "Segunda" or d == "segunda":
                        flag = 0
                        if a <= 12:
                            x = v * 0.5
                            r = "desconto crianca segunda"
                        else:
                            if a >= 60:
                                x = v * 0.5
                                r = "desconto idoso segunda"
                            else:
                                if e == True:
                                    x = v * 0.5
                                    r = "desconto estudante segunda"
                                else:
                                    x = v
                                    r = "sem desconto segunda"
                    else:
                        if d == "Terça-feira" or d == "terça-feira" or d == "Terca-feira" or d == "terca-feira" or d == "Terça" or d == "terça":
                            flag = 0
                            if a <= 12:
                                x = v * 0.5
                                r = "desconto crianca terca"
                            else:
                                if a >= 60:
                                    x = v * 0.5
                                    r = "desconto idoso terca"
                                else:
                                    if e == True:
                                        x = v * 0.5
                                        r = "desconto estudante terca"
                                    else:
                                        x = v
                                        r = "sem desconto terca"
                        else:
                            if d == "Quinta-feira" or d == "quinta-feira" or d == "Quinta" or d == "quinta":
                                flag = 0
                                if a <= 12:
                                    x = v * 0.5
                                    r = "desconto crianca quinta"
                                else:
                                    if a >= 60:
                                        x = v * 0.5
                                        r = "desconto idoso quinta"
                                    else:
                                        if e == True:
                                            x = v * 0.5
                                            r = "desconto estudante quinta"
                                        else:
                                            x = v
                                            r = "sem desconto quinta"
                            else:
                                if d == "Sexta-feira" or d == "sexta-feira" or d == "Sexta" or d == "sexta":
                                    flag = 0
                                    if a <= 12:
                                        x = v * 0.5
                                        r = "desconto crianca sexta"
                                    else:
                                        if a >= 60:
                                            x = v * 0.5
                                            r = "desconto idoso sexta"
                                        else:
                                            if e == True:
                                                x = v * 0.5
                                                r = "desconto estudante sexta"
                                            else:
                                                x = v
                                                r = "sem desconto sexta"
                                else:
                                    if d == "Sábado" or d == "sabado" or d == "Sabado" or d == "sábado":
                                        flag = 0
                                        if a <= 12:
                                            x = v * 0.5
                                            r = "desconto crianca sabado"
                                        else:
                                            if a >= 60:
                                                x = v * 0.5
                                                r = "desconto idoso sabado"
                                            else:
                                                if e == True:
                                                    x = v * 0.5
                                                    r = "desconto estudante sabado"
                                                else:
                                                    x = v
                                                    r = "sem desconto sabado"
                                    else:
                                        if d == "Domingo" or d == "domingo":
                                            flag = 0
                                            if a <= 12:
                                                x = v * 0.5
                                                r = "desconto crianca domingo"
                                            else:
                                                if a >= 60:
                                                    x = v * 0.5
                                                    r = "desconto idoso domingo"
                                                else:
                                                    if e == True:
                                                        x = v * 0.5
                                                        r = "desconto estudante domingo"
                                                    else:
                                                        x = v
                                                        r = "sem desconto domingo"
                                        else:
                                            print("Erro: dia da semana desconhecido: " + str(d))
                                            return None

    aux = x

    # geracao aleatoria e confusa do id do bilhete, misturando varias coisas
    y = random.randint(1000, 9999)
    z = str(a) + str(y) + str(int(v * 100))
    w = ""
    for i in range(len(z)):
        if i % 2 == 0:
            w = w + z[i]
    if len(w) < 4:
        w = w + "000" + str(y)
    id_bilhete = "ING-" + str(d)[0:3].upper() + "-" + w + "-" + str(y)

    if e == True:
        temp = temp + " | estudante=SIM"
    else:
        temp = temp + " | estudante=NAO"

    if a <= 12:
        msg = "Cliente crianca"
    else:
        if a >= 60:
            msg = "Cliente idoso"
        else:
            msg = "Cliente padrao"

    print("=====================================")
    print("Sistema de Venda de Ingressos - Cinema")
    print("=====================================")
    print("Valor base: R$" + str(v))
    print("Idade: " + str(a))
    print("Dia: " + str(d))
    print("Estudante: " + str(e))
    print("Categoria: " + msg)
    print("Regra aplicada: " + str(r))
    print("Valor final: R$" + str(round(aux, 2)))
    print("ID do bilhete: " + id_bilhete)
    print("=====================================")

    resultado_final = {}
    resultado_final["valor_base"] = v
    resultado_final["idade"] = a
    resultado_final["dia"] = d
    resultado_final["estudante"] = e
    resultado_final["valor_final"] = round(aux, 2)
    resultado_final["id_bilhete"] = id_bilhete
    resultado_final["regra"] = r

    return resultado_final


def main():
    print("Teste 1:")
    f(20.0, 25, "Quarta-feira", False)
    print("")
    print("Teste 2:")
    f(20.0, 10, "Sexta-feira", False)
    print("")
    print("Teste 3:")
    f(20.0, 65, "Segunda-feira", True)
    print("")
    print("Teste 4:")
    f(20.0, 30, "Domingo", True)
    print("")
    print("Teste 5:")
    f(20.0, 30, "Sabado", False)


if __name__ == "__main__":
    main()