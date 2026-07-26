"""
Rastreador de Gastos Pessoais - CLI
Salva receitas e despesas em um arquivo CSV, calcula o saldo
e mostra um resumo por categoria.
"""

import csv
import os
import json
from datetime import datetime

ARQUIVO_CSV = "transacoes.csv"
CAMPOS = ["data", "tipo", "categoria", "descricao", "valor"]


def inicializar_arquivo():
    if not os.path.exists(ARQUIVO_CSV):
        with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=CAMPOS)
            escritor.writeheader()


def parse_date(text):
    text = text.strip()
    if not text:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def adicionar_transacao():
    tipo = input("Tipo (receita/despesa): ").strip().lower()
    if tipo not in ("receita", "despesa"):
        print("Tipo inválido. Use 'receita' ou 'despesa'.\n")
        return

    data_text = input("Data (dd/mm/aaaa) [vazio = hoje]: ").strip()
    data = parse_date(data_text) if data_text else datetime.now().date()
    if data is None:
        print("Data inválida. Use dd/mm/aaaa ou aaaa-mm-dd.\n")
        return

    categoria = input("Categoria (ex: alimentação, transporte, salário): ").strip()
    descricao = input("Descrição: ").strip()

    try:
        valor = float(input("Valor: R$ ").replace(",", "."))
    except ValueError:
        print("Valor inválido.\n")
        return

    with open(ARQUIVO_CSV, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writerow({
            "data": data.strftime("%d/%m/%Y"),
            "tipo": tipo,
            "categoria": categoria,
            "descricao": descricao,
            "valor": f"{valor:.2f}",
        })

    print("Transação registrada com sucesso!\n")


def ler_transacoes():
    if not os.path.exists(ARQUIVO_CSV):
        return []
    with open(ARQUIVO_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def salvar_transacoes(transacoes):
    with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        for t in transacoes:
            escritor.writerow(t)


def mostrar_resumo(export_json=False):
    transacoes = ler_transacoes()
    if not transacoes:
        print("Nenhuma transação registrada ainda.\n")
        return

    total_receitas = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "receita")
    total_despesas = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "despesa")
    saldo = total_receitas - total_despesas

    resumo_categoria = {}
    for t in transacoes:
        if t["tipo"] == "despesa":
            resumo_categoria[t["categoria"]] = resumo_categoria.get(t["categoria"], 0) + float(t["valor"])

    resumo = {
        "total_receitas": round(total_receitas, 2),
        "total_despesas": round(total_despesas, 2),
        "saldo": round(saldo, 2),
        "despesas_por_categoria": {k: round(v, 2) for k, v in resumo_categoria.items()},
    }

    print("\n--- RESUMO FINANCEIRO ---")
    print(f"Total de receitas: R$ {resumo['total_receitas']:.2f}")
    print(f"Total de despesas: R$ {resumo['total_despesas']:.2f}")
    print(f"Saldo atual: R$ {resumo['saldo']:.2f}")

    if resumo_categoria:
        print("\n--- DESPESAS POR CATEGORIA ---")
        for categoria, valor in sorted(resumo_categoria.items(), key=lambda x: -x[1]):
            print(f"{categoria}: R$ {valor:.2f}")
    print()

    if export_json:
        with open("resumo.json", "w", encoding="utf-8") as f:
            json.dump(resumo, f, ensure_ascii=False, indent=2)
        print("Resumo exportado para resumo.json\n")


def listar_transacoes(start_date=None, end_date=None, categoria_filter=None):
    transacoes = ler_transacoes()
    if not transacoes:
        print("Nenhuma transação registrada ainda.\n")
        return []

    def in_range(t):
        try:
            d = datetime.strptime(t["data"], "%d/%m/%Y").date()
        except Exception:
            return False
        if start_date and d < start_date:
            return False
        if end_date and d > end_date:
            return False
        if categoria_filter and t["categoria"].lower() != categoria_filter.lower():
            return False
        return True

    filtradas = [t for t in transacoes if in_range(t)]

    print("\n--- TRANSAÇÕES ---")
    for i, t in enumerate(filtradas, 1):
        sinal = "+" if t["tipo"] == "receita" else "-"
        print(f"{i:3d}. {t['data']} | {t['categoria']:<15} | {t['descricao']:<25} | {sinal}R$ {float(t['valor']):.2f}")
    print()
    return filtradas


def editar_transacao():
    all_trans = ler_transacoes()
    if not all_trans:
        print("Nenhuma transação para editar.\n")
        return

    listar_transacoes()
    try:
        idx = int(input("Número da transação a editar: ")) - 1
    except ValueError:
        print("Índice inválido.\n")
        return

    filtradas = ler_transacoes()
    if idx < 0 or idx >= len(filtradas):
        print("Índice fora do intervalo.\n")
        return

    t = filtradas[idx]
    print("Deixe vazio para manter o valor atual.")
    nova_data = input(f"Data ({t['data']}): ").strip()
    if nova_data:
        d = parse_date(nova_data)
        if not d:
            print("Data inválida. Edição abortada.\n")
            return
        t['data'] = d.strftime("%d/%m/%Y")

    novo_tipo = input(f"Tipo ({t['tipo']}): ").strip().lower()
    if novo_tipo:
        if novo_tipo not in ("receita", "despesa"):
            print("Tipo inválido. Edição abortada.\n")
            return
        t['tipo'] = novo_tipo

    nova_cat = input(f"Categoria ({t['categoria']}): ").strip()
    if nova_cat:
        t['categoria'] = nova_cat

    nova_desc = input(f"Descrição ({t['descricao']}): ").strip()
    if nova_desc:
        t['descricao'] = nova_desc

    novo_valor = input(f"Valor (R$ {t['valor']}): ").strip()
    if novo_valor:
        try:
            v = float(novo_valor.replace(",", "."))
            t['valor'] = f"{v:.2f}"
        except ValueError:
            print("Valor inválido. Edição abortada.\n")
            return

    salvar_transacoes(filtradas)
    print("Transação atualizada com sucesso!\n")


def excluir_transacao():
    transacoes = ler_transacoes()
    if not transacoes:
        print("Nenhuma transação para excluir.\n")
        return

    listar_transacoes()
    try:
        idx = int(input("Número da transação a excluir: ")) - 1
    except ValueError:
        print("Índice inválido.\n")
        return

    if idx < 0 or idx >= len(transacoes):
        print("Índice fora do intervalo.\n")
        return

    del transacoes[idx]
    salvar_transacoes(transacoes)
    print("Transação excluída com sucesso!\n")


def exportar_transacoes():
    print("Exportar transações — deixe filtros vazios para exportar tudo.")
    inicio = parse_date(input("Data início (dd/mm/aaaa) [vazio]: ").strip() or "")
    fim = parse_date(input("Data fim (dd/mm/aaaa) [vazio]: ").strip() or "")
    cat = input("Categoria [vazio = todas]: ").strip() or None

    filtradas = listar_transacoes(inicio, fim, cat)
    if not filtradas:
        print("Nada para exportar.\n")
        return

    nome = input("Nome do arquivo de saída (ex: export.csv): ").strip() or "export.csv"
    with open(nome, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        for t in filtradas:
            escritor.writerow(t)

    print(f"Exportado {len(filtradas)} transações para {nome}\n")


def menu():
    inicializar_arquivo()
    while True:
        print("===== RASTREADOR DE GASTOS PESSOAIS =====")
        print("1 - Adicionar transação")
        print("2 - Listar transações (com filtros)")
        print("3 - Ver resumo financeiro")
        print("4 - Editar transação")
        print("5 - Excluir transação")
        print("6 - Exportar transações")
        print("7 - Exportar resumo para JSON")
        print("8 - Sair")
        escolha = input("Escolha uma opção: ").strip()

        if escolha == "1":
            adicionar_transacao()
        elif escolha == "2":
            inicio = parse_date(input("Data início (dd/mm/aaaa) [vazio]: ").strip() or "")
            fim = parse_date(input("Data fim (dd/mm/aaaa) [vazio]: ").strip() or "")
            cat = input("Categoria [vazio = todas]: ").strip() or None
            listar_transacoes(inicio, fim, cat)
        elif escolha == "3":
            mostrar_resumo()
        elif escolha == "4":
            editar_transacao()
        elif escolha == "5":
            excluir_transacao()
        elif escolha == "6":
            exportar_transacoes()
        elif escolha == "7":
            mostrar_resumo(export_json=True)
        elif escolha == "8":
            print("Até logo!")
            break
        else:
            print("Opção inválida.\n")


if __name__ == "__main__":
    menu()
