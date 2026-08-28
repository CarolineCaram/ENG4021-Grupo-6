import soma
import subtrai
import multiplicacao
import divisao

aux=int(input("Informe a operação desejada:\n1-Soma\n2-Subtracao\n3-Multiplicacao\n4-Divisao\n"))
if(aux==1):
    resultado=int(soma.somaf())
    print(f"Resultado: {resultado}")
elif(aux==2):
    resultado=int(subtracao.subtracaof())
    print(f"Resultado: {resultado}")
elif(aux==3):
    resultado=int(multiplicacao.multiplicacaof())
    print(f"Resultado: {resultado}")
elif(aux==4):
    resultado=int(divisao.divisaof())
    print(f"Resultado: {resultado}")


    



