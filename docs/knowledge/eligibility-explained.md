# Academic Demo — Preliminary Eligibility

Loan eligibility is calculated from five checks: income must meet the selected product minimum, requested amount and tenure must be within its configured ranges, employment must be salaried or self_employed, and (rounded monthly installment + existing monthly obligations) / monthly income must not exceed the product max_dti threshold; all five must pass, without guaranteeing approval.

Eligibility repayment capacity is assessed using EMI = P*r*(1+r)^n/((1+r)^n-1), where P is requested amount, r is the product annual percentage rate / 1200 and n is months; at zero interest EMI = P/n, rounded half-up to two decimals, with estimated repayment equal to rounded EMI times n.

These are academic INR estimates from self-reported synthetic inputs, with fixed indicative interest and no credit-bureau check; fees, insurance and taxes are excluded.

Product minimum income, amount and tenure limits, interest rate and max_dti come from the selected active product, not a universal policy; consult the current catalog because administrators can change product configuration.

Input validation accepts positive monthly income up to INR 10000000, obligations from zero to INR 10000000, positive amount up to INR 100000000, and tenure from 1 to 360 months; monetary inputs permit two decimal places.

Input validation accepts salaried, self_employed, student and unemployed employment values, but only the first two pass the regular-income eligibility check.

A preliminary result is separate from draft creation and submission; final approval or rejection requires an authorized human reviewer and is never guaranteed by valid inputs.
