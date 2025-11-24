import json
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

LOG_FILE = "finance.log"

logger = logging.getLogger("finance_app")
logger.setLevel(logging.DEBUG)  # captura tudo; handlers filtram o que mostrar

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
file_handler.setLevel(logging.INFO)  # grava INFO+ no arquivo
file_handler.setFormatter(formatter)


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

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
        logger.debug("Inicializando FinanceManager com arquivo %s", data_file)
        self._load()


    def _load(self) -> None:
        """Carrega dados do arquivo JSON."""
        if not self.data_file.exists():
            logger.info("Arquivo de dados %s não encontrado. Criando novo.", self.data_file)
            self._save()  # cria arquivo vazio
            return

        try:
            with self.data_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.transactions = [Transaction.from_dict(t) for t in data]
            logger.info("Carregadas %d transações do arquivo.", len(self.transactions))
        except json.JSONDecodeError as e:
            logger.error("Erro ao decodificar JSON: %s", e)
            self.transactions = []
        except Exception as e:
            logger.exception("Erro inesperado ao carregar dados: %s", e)
            self.transactions = []

    def _save(self) -> None:
        """Salva dados no arquivo JSON."""
        try:
            data = [asdict(t) for t in self.transactions]
            with self.data_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Dados salvos com sucesso (%d transações).", len(self.transactions))
        except Exception as e:
            logger.exception("Erro ao salvar dados: %s", e)


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
        logger.debug(
            "Solicitada adição de transação: type=%s category=%s desc=%s amount=%.2f date=%s",
            type_, category, description, amount, date,
        )

        type_ = type_.lower()
        if type_ not in ("entrada", "saida"):
            logger.error("Tipo de transação inválido: %s", type_)
            raise ValueError("Tipo deve ser 'entrada' ou 'saida'.")

        if amount <= 0:
            logger.error("Valor inválido para transação: %.2f", amount)
            raise ValueError("Valor deve ser positivo.")

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            # valida formato
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                logger.error("Data inválida: %s (esperado YYYY-MM-DD)", date)
                raise

        new_transaction = Transaction(
            id=self._next_id(),
            date=date,
            type=type_,
            category=category.strip(),
            description=description.strip(),
            amount=amount,
        )

        self.transactions.append(new_transaction)
        logger.info("Transação adicionada: %s", new_transaction)
        self._save()
        return new_transaction

    def list_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        type_: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Transaction]:
        """Lista transações com filtros opcionais."""
        logger.debug(
            "Listando transações com filtros: start_date=%s end_date=%s type=%s category=%s",
            start_date, end_date, type_, category,
        )

        filtered = self.transactions

        def parse_date(d: str) -> datetime:
            return datetime.strptime(d, "%Y-%m-%d")

        if start_date:
            try:
                d0 = parse_date(start_date)
                filtered = [t for t in filtered if parse_date(t.date) >= d0]
            except ValueError:
                logger.warning("Data inicial inválida para filtro: %s", start_date)

        if end_date:
            try:
                d1 = parse_date(end_date)
                filtered = [t for t in filtered if parse_date(t.date) <= d1]
            except ValueError:
                logger.warning("Data final inválida para filtro: %s", end_date)

        if type_:
            type_ = type_.lower()
            filtered = [t for t in filtered if t.type == type_]

        if category:
            filtered = [t for t in filtered if t.category.lower() == category.lower()]

        logger.info(" Foram encontradas %d transações com os filtros aplicados.", len(filtered))
        return filtered

    def get_summary(self) -> dict:
        """Retorna resumo: total de entradas, saídas e saldo."""
        total_entradas = sum(t.amount for t in self.transactions if t.type == "entrada")
        total_saidas = sum(t.amount for t in self.transactions if t.type == "saida")
        saldo = total_entradas - total_saidas

        logger.info(
            "Resumo calculado: entradas=%.2f saídas=%.2f saldo=%.2f",
            total_entradas, total_saidas, saldo
        )

        return {
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "saldo": saldo,
            "qtd_transacoes": len(self.transactions),
        }



def input_float(msg: str) -> float:
    while True:
        value = input(msg).strip().replace(",", ".")
        try:
            val = float(value)
            logger.debug("Usuário informou valor numérico: %s -> %.2f", value, val)
            return val
        except ValueError:
            logger.warning("Entrada inválida para float: %s", value)
            print("Valor inválido. Tente novamente.")


def input_date(msg: str, allow_empty: bool = True) -> Optional[str]:
    while True:
        value = input(msg).strip()
        if allow_empty and value == "":
            return None
        try:
            datetime.strptime(value, "%Y-%m-%d")
            logger.debug("Usuário informou data válida: %s", value)
            return value
        except ValueError:
            logger.warning("Entrada de data inválida: %s", value)
            print("Data inválida. Use o formato YYYY-MM-DD (ex: 2025-11-24).")


def show_transactions(transactions: List[Transaction]) -> None:
    if not transactions:
        print("Nenhuma transação encontrada.")
        return

    print("\nID | Data       | Tipo    | Categoria       | Valor      | Descrição")
    print("-" * 75)
    for t in transactions:
        print(
            f"{t.id:2d} | {t.date} | {t.type:<7} | {t.category:<14} | "
            f"R$ {t.amount:8.2f} | {t.description}"
        )
    print("-" * 75)
    print(f"Total de transações listadas: {len(transactions)}\n")


def main_menu():
    fm = FinanceManager()
    logger.info("Aplicação iniciada.")

    while True:
        print("\n=== SISTEMA DE CONTROLE FINANCEIRO PESSOAL ===")
        print("1 - Adicionar transação")
        print("2 - Listar todas as transações")
        print("3 - Listar transações filtradas")
        print("4 - Ver resumo (entradas, saídas, saldo)")
        print("5 - Sair")
        choice = input("Escolha uma opção: ").strip()

        try:
            if choice == "1":
                type_ = input("Tipo (entrada/saida): ").strip().lower()
                category = input("Categoria (ex: Salário, Mercado, Lazer): ").strip()
                description = input("Descrição: ").strip()
                amount = input_float("Valor (use ponto ou vírgula): ")
                date = input_date("Data (YYYY-MM-DD) ou deixe em branco para hoje: ")

                transaction = fm.add_transaction(
                    type_=type_,
                    category=category,
                    description=description,
                    amount=amount,
                    date=date,
                )
                print(f"\nTransação adicionada com sucesso! ID: {transaction.id}")

            elif choice == "2":
                trans = fm.list_transactions()
                show_transactions(trans)

            elif choice == "3":
                print("\n=== FILTROS ===")
                start_date = input_date(
                    "Data inicial (YYYY-MM-DD) ou deixe em branco: ", allow_empty=True
                )
                end_date = input_date(
                    "Data final (YYYY-MM-DD) ou deixe em branco: ", allow_empty=True
                )
                type_ = input("Tipo (entrada/saida) ou deixe em branco: ").strip().lower()
                type_ = type_ if type_ in ("entrada", "saida") else None
                category = input("Categoria exata ou deixe em branco: ").strip()
                category = category if category else None

                trans = fm.list_transactions(
                    start_date=start_date,
                    end_date=end_date,
                    type_=type_,
                    category=category,
                )
                show_transactions(trans)

            elif choice == "4":
                summary = fm.get_summary()
                print("\n=== RESUMO GERAL ===")
                print(f"Total de entradas: R$ {summary['total_entradas']:.2f}")
                print(f"Total de saídas : R$ {summary['total_saidas']:.2f}")
                print(f"Saldo           : R$ {summary['saldo']:.2f}")
                print(f"Qtd transações  : {summary['qtd_transacoes']}")

            elif choice == "5":
                logger.info("Usuário escolheu sair da aplicação.")
                print("Saindo... até mais!")
                break

            else:
                logger.warning("Opção de menu inválida: %s", choice)
                print("Opção inválida. Tente novamente.")

        except Exception as e:

            logger.exception("Erro na opção de menu %s: %s", choice, e)
            print(f"Ocorreu um erro: {e}. Verifique o log para mais detalhes.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        logger.warning("Aplicação interrompida pelo usuário (KeyboardInterrupt).")
        print("\nAplicação encerrada pelo usuário.")
    except Exception as e:
        logger.critical("Erro crítico ao executar a aplicação: %s", e, exc_info=True)
        print(f"Erro crítico: {e}. Veja o arquivo de log.")
