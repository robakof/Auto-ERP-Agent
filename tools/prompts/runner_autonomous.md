{role}
[TRYB AUTONOMICZNY — brak interakcji z użytkownikiem]
[TASK od: {sender}]
[ADRES ZWROTNY: {instance_id}]

Uruchom session_init --role {role}.

Gdy session_start mówi "Czekaj na instrukcję od użytkownika" — Twoja instrukcja to task poniżej.
Nie czekaj na kolejną wiadomość. Realizuj task zgodnie ze swoim workflow.

Task do realizacji:
{content}

Gdy skończysz — zaloguj przez agent_bus i zakończ sesję.
