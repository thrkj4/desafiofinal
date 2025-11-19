import json
from datetime import datetime
from pathlib import Path

ARQUIVO_DADOS = Path("transacoes.json")


def carregar_transacoes():
    if ARQUIVO_DADOS.exists():
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_transacoes(transacoes):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(transacoes, f, ensure_ascii=False, indent=4)



def ler_data(msg="Data (dd/mm/aaaa): "):
    while True:
        data_str = input(msg).strip()
        try:
            data = datetime.strptime(data_str, "%d/%m/%Y")
            return data_str  # guardar como string
        except ValueError:
            print("Data inválida. Use o formato dd/mm/aaaa.")


def ler_tipo():
    while True:
        tipo = input("Tipo (E para entrada / S para saída): ").strip().upper()
        if tipo in ("E", "S"):
            return "entrada" if tipo == "E" else "saida"
        print("Opção inválida. Digite E ou S.")


def ler_valor():
    while True:
        valor_str = input("Valor: ").replace(",", ".").strip()
        try:
            valor = float(valor_str)
            return valor
        except ValueError:
            print("Valor inválido. Digite um número.")



def adicionar_transacao(transacoes):
    print("\n--- Adicionar transação ---")
    data = ler_data()
    tipo = ler_tipo()
    categoria = input("Categoria: ").strip()
    descricao = input("Descrição: ").strip()
    valor = ler_valor()

    transacao = {
        "data": data,
        "tipo": tipo,
        "categoria": categoria,
        "descricao": descricao,
        "valor": valor,
    }
    transacoes.append(transacao)
    salvar_transacoes(transacoes)
    print("Transação adicionada com sucesso!\n")


def listar_transacoes(transacoes):
    if not transacoes:
        print("\nNenhuma transação cadastrada.\n")
        return

    print("\n--- Todas as transações ---")
    for i, t in enumerate(transacoes, start=1):
        print(f"{i}. {t['data']} | {t['tipo']} | {t['categoria']} | "
              f"{t['descricao']} | R$ {t['valor']:.2f}")
    print()


def remover_transacao(transacoes):
    listar_transacoes(transacoes)
    if not transacoes:
        return

    while True:
        try:
            idx = int(input("Número da transação para remover (0 para cancelar): "))
            if idx == 0:
                print("Operação cancelada.\n")
                return
            if 1 <= idx <= len(transacoes):
                removida = transacoes.pop(idx - 1)
                salvar_transacoes(transacoes)
                print(f"Transação removida: {removida['descricao']}\n")
                return
            else:
                print("Número inválido.")
        except ValueError:
            print("Digite um número válido.")


def listar_por_categoria(transacoes):
    if not transacoes:
        print("\nNenhuma transação cadastrada.\n")
        return

    categoria = input("\nCategoria para filtrar: ").strip()
    filtradas = [t for t in transacoes if t["categoria"].lower() == categoria.lower()]

    if not filtradas:
        print("Nenhuma transação encontrada para essa categoria.\n")
        return

    print(f"\n--- Transações da categoria '{categoria}' ---")
    for t in filtradas:
        print(f"{t['data']} | {t['tipo']} | {t['descricao']} | R$ {t['valor']:.2f}")
    print()


def ler_periodo():
    print("\nInforme o período:")
    inicio = ler_data("Data inicial (dd/mm/aaaa): ")
    fim = ler_data("Data final   (dd/mm/aaaa): ")

    d_inicio = datetime.strptime(inicio, "%d/%m/%Y")
    d_fim = datetime.strptime(fim, "%d/%m/%Y")

    if d_fim < d_inicio:
        print("Período inválido: data final menor que a inicial.\n")
        return None, None, None

    return inicio, fim, (d_inicio, d_fim)


def filtrar_por_periodo(transacoes, periodo):
    d_inicio, d_fim = periodo
    filtradas = []
    for t in transacoes:
        d_t = datetime.strptime(t["data"], "%d/%m/%Y")
        if d_inicio <= d_t <= d_fim:
            filtradas.append(t)
    return filtradas


def listar_transacoes_por_periodo(transacoes):
    if not transacoes:
        print("\nNenhuma transação cadastrada.\n")
        return

    inicio_str, fim_str, periodo = ler_periodo()
    if periodo is None:
        return

    filtradas = filtrar_por_periodo(transacoes, periodo)

    if not filtradas:
        print("Nenhuma transação nesse período.\n")
        return

    print(f"\n--- Transações de {inicio_str} até {fim_str} ---")
    for t in filtradas:
        print(f"{t['data']} | {t['tipo']} | {t['categoria']} | "
              f"{t['descricao']} | R$ {t['valor']:.2f}")
    print()


def calcular_saldo_por_periodo(transacoes):
    if not transacoes:
        print("\nNenhuma transação cadastrada.\n")
        return

    inicio_str, fim_str, periodo = ler_periodo()
    if periodo is None:
        return

    filtradas = filtrar_por_periodo(transacoes, periodo)

    saldo = 0.0
    for t in filtradas:
        if t["tipo"] == "entrada":
            saldo += t["valor"]
        else:  # saida
            saldo -= t["valor"]

    print(f"\nSaldo de {inicio_str} até {fim_str}: R$ {saldo:.2f}\n")



def mostrar_menu():
    print("=== Sistema de Controle Financeiro Pessoal ===")
    print("1 - Adicionar transação")
    print("2 - Remover transação")
    print("3 - Listar transações por categoria")
    print("4 - Listar transações por período")
    print("5 - Calcular saldo por período")
    print("6 - Listar todas as transações")
    print("0 - Sair")


def main():
    transacoes = carregar_transacoes()

    while True:
        mostrar_menu()
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            adicionar_transacao(transacoes)
        elif opcao == "2":
            remover_transacao(transacoes)
        elif opcao == "3":
            listar_por_categoria(transacoes)
        elif opcao == "4":
            listar_transacoes_por_periodo(transacoes)
        elif opcao == "5":
            calcular_saldo_por_periodo(transacoes)
        elif opcao == "6":
            listar_transacoes(transacoes)
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.\n")


if __name__ == "__main__":
    main()
