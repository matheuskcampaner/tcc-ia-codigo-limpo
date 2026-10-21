import random

def p(a, b, c, d):
    # a = valor base, b = idade, c = dia, d = eh estudante
    
    # Validação e Processamento tudo junto
    if a != None:
        if type(a) == int or type(a) == float:
            if a > 0:
                if b != None and type(b) == int and b >= 0:
                    if c != None and type(c) == str:
                        temp_dia = c.lower().strip()
                        if temp_dia == 'segunda-feira' or temp_dia == 'terça-feira' or temp_dia == 'quarta-feira' or temp_dia == 'quinta-feira' or temp_dia == 'sexta-feira' or temp_dia == 'sábado' or temp_dia == 'domingo':
                            if d == True or d == False:
                                
                                # Lógica de cálculo bagunçada e aninhada
                                aux = a
                                flag = 0
                                
                                if temp_dia == 'quarta-feira':
                                    # Desconto de quarta
                                    aux = a * 0.5
                                    flag = 1
                                    print("Desconto de quarta-feira aplicado!")
                                else:
                                    # Checa estudante
                                    if d == True:
                                        aux = a * 0.5
                                        flag = 1
                                        print("Desconto de estudante aplicado!")
                                    else:
                                        # Checa idade se não for estudante
                                        if b <= 12:
                                            aux = a * 0.5
                                            flag = 1
                                            print("Desconto infantil aplicado!")
                                        else:
                                            if b >= 60:
                                                aux = a * 0.5
                                                flag = 1
                                                print("Desconto idoso aplicado!")
                                            else:
                                                aux = a
                                                flag = 0
                                                print("Sem desconto aplicado.")
                                
                                # Geração de ID gambiarra no meio do fluxo
                                x1 = str(random.randint(100, 999))
                                x2 = str(b)
                                x3 = temp_dia[0:2].upper()
                                id_final = "TKT-" + x3 + "-" + x1 + "-" + x2
                                
                                # Impressão direta do comprovante no final da função
                                print("--------------------------------")
                                print("BILHETE GERADO: " + id_final)
                                print("Idade: " + str(b))
                                print("Dia: " + c)
                                print("Valor Original: R$ " + str(a))
                                print("Valor Final: R$ " + str(aux))
                                print("--------------------------------")
                                
                                return aux
                            else:
                                print("Erro: parâmetro estudante inválido")
                                return -1
                        else:
                            print("Erro: dia da semana inválido")
                            return -1
                    else:
                        print("Erro: dia nulo ou tipo incorreto")
                        return -1
                else:
                    print("Erro: idade inválida")
                    return -1
            else:
                print("Erro: valor base deve ser maior que zero")
                return -1
        else:
            print("Erro: valor base deve ser numérico")
            return -1
    else:
        print("Erro: valor base nulo")
        return -1

# --- TESTES RÁPIDOS ---
print("--- TESTE 1: Quarta-feira (Geral) ---")
p(30.0, 25, 'Quarta-feira', False)

print("\n--- TESTE 2: Estudante em outro dia ---")
p(30.0, 20, 'Sábado', True)

print("\n--- TESTE 3: Idoso sem cumulatividade (Quarta) ---")
p(40.0, 65, 'quarta-feira', True)

print("\n--- TESTE 4: Sem desconto ---")
p(20.0, 30, 'Sexta-feira', False)