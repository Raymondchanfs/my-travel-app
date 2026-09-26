import json
from decimal import ROUND_HALF_UP, Decimal


def targets(v):
    try:
        x = json.loads(str(v))
        return x if isinstance(x, list) else []
    except:
        return [i.strip() for i in str(v).split(",") if i.strip()]


def settlement(expenses, members):
    paid = {m: Decimal(0) for m in members}
    share = {m: Decimal(0) for m in members}
    for _, e in expenses.iterrows():
        try:
            amount = Decimal(str(e.get("base_amount", 0)))
        except:
            continue
        payer = str(e.get("payer", ""))
        people = (
            members
            if e.get("split_type") == "全體均分"
            else [x for x in targets(e.get("split_members", "")) if x in members]
        )
        if payer in paid:
            paid[payer] += amount
        if people:
            for m in people:
                share[m] += amount / len(people)
    balance = {
        m: (paid[m] - share[m]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for m in members
    }
    debt = [[m, -v] for m, v in balance.items() if v < 0]
    credit = [[m, v] for m, v in balance.items() if v > 0]
    out = []
    i = j = 0
    while i < len(debt) and j < len(credit):
        a = min(debt[i][1], credit[j][1])
        out.append(
            {
                "付款人": debt[i][0],
                "收款人": credit[j][0],
                "金額": a.quantize(Decimal("0.01")),
            }
        )
        debt[i][1] -= a
        credit[j][1] -= a
        if debt[i][1] <= 0:
            i += 1
        if credit[j][1] <= 0:
            j += 1
    return paid, share, balance, out
