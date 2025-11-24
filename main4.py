import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from collections import defaultdict, OrderedDict
import matplotlib.pyplot as plt


DATA_FILE = Path("finance_data.json")


@dataclass
class Transaction:
    id: int
    date: str        # "YYYY-MM-DD"
    type: str        # "entrada" ou "saida"
    category: str
    description: str
    amount: float    # valor positivo

    @staticmethod
    def from_dict(data: dict) -> "Transaction":
        return Transaction(
            id=int(data["id"]),
            date=data["date"],
            type=data["type"],
            category=data["category"],
            description=data["description"],
            amount=float(data["amount"]),
        )


class FinanceManager:
    def __init__(self, data_file: Path = DATA_FILE):
        self.data_file = data_file
        self.transactions: List[Transaction] = []
        self._load()



    def _load(self) -> None:
        """Carrega dados do arquivo JSON."""
        if not self.data_file.exists():
            self._save()  # cria arquivo vazio
            return

        try:
            with self.data_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.transactions = [Transaction.from_dict(t) for t in data]
        except Exception:
            self.transactions = []

    def _save(self) -> None:
        """Salva dados no arquivo JSON."""
        data = [asdict(t) for t in self.transactions]
        with self.data_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)



    def _next_id(self) -> int:
        if not self.transactions:
            return 1
        return max(t.id for t in self.transactions) + 1

    def add_transaction(
        self,
        type_: str,
        category: str,
        description: str,
        amount: float,
        date: Optional[str] = None,
    ) -> Transaction:
        """Adiciona uma nova transação."""
        type_ = type_.lower()
        if type_ not in ("entrada", "saida"):
            raise ValueError("Tipo deve ser 'entrada' ou 'saida'.")

        if amount <= 0:
            raise ValueError("Valor deve ser positivo.")

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            # valida formato
            datetime.strptime(date, "%Y-%m-%d")

        new_transaction = Transaction(
            id=self._next_id(),
            date=date,
            type=type_,
            category=category.strip() or "Outros",
            description=description.strip(),
            amount=amount,
        )

        self.transactions.append(new_transaction)
        self._save()
        return new_transaction

    def list_transactions(self) -> List[Transaction]:
        return list(self.transactions)


    def get_basic_stats(self) -> Dict[str, float]:
        """Retorna estatísticas básicas do sistema."""
        total_receitas = sum(t.amount for t in self.transactions if t.type == "entrada")
        total_despesas = sum(t.amount for t in self.transactions if t.type == "saida")
        saldo_atual = total_receitas - total_despesas

        gastos = [t.amount for t in self.transactions if t.type == "saida"]

        media_gasto_transacao = sum(gastos) / len(gastos) if gastos else 0.0

        # média de gastos por mês (somando gastos por mês e tirando média dos meses)
        gastos_por_mes = self._monthly_expenses()
        if gastos_por_mes:
            media_gasto_mensal = sum(gastos_por_mes.values()) / len(gastos_por_mes)
        else:
            media_gasto_mensal = 0.0

        return {
            "total_receitas": total_receitas,
            "total_despesas": total_despesas,
            "saldo_atual": saldo_atual,
            "media_gasto_transacao": media_gasto_transacao,
            "media_gasto_mensal": media_gasto_mensal,
            "qtd_transacoes": len(self.transactions),
        }



    def _monthly_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Retorna um dict:
        {
          "YYYY-MM": {"entradas": ..., "saidas": ..., "saldo": ...},
          ...
        }
        """
        resumo: Dict[str, Dict[str, float]] = defaultdict(lambda: {"entradas": 0.0, "saidas": 0.0, "saldo": 0.0})

        for t in self.transactions:
            dt = datetime.strptime(t.date, "%Y-%m-%d")
            chave = dt.strftime("%Y-%m")  # exemplo: "2025-11"

            if t.type == "entrada":
                resumo[chave]["entradas"] += t.amount
            elif t.type == "saida":
                resumo[chave]["saidas"] += t.amount

        for mes, dados in resumo.items():
            dados["saldo"] = dados["entradas"] - dados["saidas"]

        # ordenar por mês
        ordenado = OrderedDict(sorted(resumo.items(), key=lambda item: item[0]))
        return ordenado

    def _monthly_expenses(self) -> Dict[str, float]:
        """Retorna dict 'YYYY-MM' -> total de despesas no mês."""
        gastos_por_mes: Dict[str, float] = defaultdict(float)

        for t in self.transactions:
            if t.type != "saida":
                continue
            dt = datetime.strptime(t.date, "%Y-%m-%d")
            chave = dt.strftime("%Y-%m")
            gastos_por_mes[chave] += t.amount

        return gastos_por_mes

    def category_expenses(self) -> Dict[str, float]:
        """Retorna um dict categoria -> total de gastos (saídas)."""
        categorias: Dict[str, float] = defaultdict(float)

        for t in self.transactions:
            if t.type == "saida":
                categorias[t.category] += t.amount

        return dict(categorias)



def plot_pizza_gastos_por_categoria(fm: FinanceManager) -> None:
    dados = fm.category_expenses()

    if not dados:
        print("Não há gastos cadastrados para gerar o gráfico de pizza.")
        return

    categorias = list(dados.keys())
    valores = list(dados.values())

    plt.figure(figsize=(8, 8))
    plt.title("Distribuição de Gastos por Categoria")
    plt.pie(valores, labels=categorias, autopct="%1.1f%%", startangle=90)
    plt.tight_layout()
    plt.show()


def plot_linha_saldo_mensal(fm: FinanceManager) -> None:
    resumo = fm._monthly_summary()

    if not resumo:
        print("Não há transações suficientes para gerar o gráfico de saldo mensal.")
        return

    meses = list(resumo.keys())
    saldos = [dados["saldo"] for dados in resumo.values()]

    plt.figure(figsize=(10, 5))
    plt.plot(meses, saldos, marker="o")
    plt.title("Saldo Mensal")
    plt.xlabel("Mês (AAAA-MM)")
    plt.ylabel("Saldo (R$)")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()



def input_float(msg: str) -> float:
    while True:
        valor = input(msg).strip().replace(",", ".")
        try:
            return float(valor)
        except ValueError:
            print("Valor inválido. Tente novamente.")


def input_date(msg: str, allow_empty: bool = True) -> Optional[str]:
    while True:
        value = input(msg).strip()
        if allow_empty and value == "":
            return None
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print("Data inválida. Use o formato YYYY-MM-DD (ex: 2025-11-24).")


def show_stats(fm: FinanceManager) -> None:
    stats = fm.get_basic_stats()
    print("\n=== ESTATÍSTICAS FINANCEIRAS ===")
    print(f"Total de RECEITAS      : R$ {stats['total_receitas']:.2f}")
    print(f"Total de DESPESAS      : R$ {stats['total_despesas']:.2f}")
    print(f"SALDO ATUAL            : R$ {stats['saldo_atual']:.2f}")
    print(f"MÉDIA de GASTO / trans.: R$ {stats['media_gasto_transacao']:.2f}")
    print(f"MÉDIA de GASTO / mês   : R$ {stats['media_gasto_mensal']:.2f}")
    print(f"Qtd total de transações: {stats['qtd_transacoes']}")
    print("===============================\n")


def show_transactions(transactions: List[Transaction]) -> None:
    if not transactions:
        print("Nenhuma transação cadastrada.")
        return

    print("\nID | Data       | Tipo    | Categoria       | Valor      | Descrição")
    print("-" * 75)
    for t in transactions:
        print(
            f"{t.id:2d} | {t.date} | {t.type:<7} | {t.category:<14} | "
            f"R$ {t.amount:8.2f} | {t.description}"
        )
    print("-" * 75)
    print(f"Total de transações: {len(transactions)}\n")


def main_menu():
    fm = FinanceManager()

    while True:
        print("\n=== SISTEMA DE CONTROLE FINANCEIRO COM GRÁFICOS ===")
        print("1 - Adicionar transação")
        print("2 - Listar transações")
        print("3 - Ver estatísticas numéricas")
        print("4 - Gráfico de pizza (gastos por categoria)")
        print("5 - Gráfico de linha (saldo mensal)")
        print("6 - Sair")
        opcao = input("Escolha uma opção: ").strip()

        try:
            if opcao == "1":
                tipo = input("Tipo (entrada/saida): ").strip().lower()
                categoria = input("Categoria (ex: Salário, Mercado, Lazer): ").strip()
                descricao = input("Descrição: ").strip()
                valor = input_float("Valor (use ponto ou vírgula): ")
                data = input_date("Data (YYYY-MM-DD) ou deixe em branco para hoje: ")

                trans = fm.add_transaction(
                    type_=tipo,
                    category=categoria,
                    description=descricao,
                    amount=valor,
                    date=data,
                )
                print(f"\nTransação adicionada com sucesso! ID: {trans.id}")

            elif opcao == "2":
                show_transactions(fm.list_transactions())

            elif opcao == "3":
                show_stats(fm)

            elif opcao == "4":
                plot_pizza_gastos_por_categoria(fm)

            elif opcao == "5":
                plot_linha_saldo_mensal(fm)

            elif opcao == "6":
                print("Saindo... até mais!")
                break

            else:
                print("Opção inválida. Tente novamente.")

        except Exception as e:
            print(f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    main_menu()
