## Tutorial - Adicionando o indicador de 'digitando'

Este tutorial mostra como o indicador de 'digitando' foi implementado no cliente. O processo de adicionar uma nova feature ao zulip terminal varia bastante dependendo da feature. Esse tutorial tem o objetivo de te tornar familiar ao processo geral.

Como os dados do indicador de 'digitando' para o outro usuário em uma mensagem privada não pode ser gerado localmente, ele deve ser recebido do cliente.

Uma pesquisa rápida no google `zulip typing indicator` nos leva para https://zulip.readthedocs.io/en/latest/subsystems/typing-indicators.html. Esse documento explica como o indicador de 'digitando' é implementado no cliente web, e é útil em entender como o ele funciona internamente.

Você pode achar a maioria das features web documentadas em https://zulip.readthedocs.io/en/latest/subsystems e entender como elas funcionam internamente.

A URL https://chat.zulip.org/api/ mostra como encontrar endpoints, e qual resposta esperar do servidor. Tem duas partes nessa feature.

Existem duas etapas em implementar o indicador de 'digitando':
* Receber o evento de digitando do servidor.
* Enviar o evento de digitando do servidor.

Nós implementaremos a primeira parte. **Receber o evento de 'digitando' do servidor**

No início da execução, o aplicativo registra os eventos do servidor que ele está disponível para assumir. Para receber atualizações para eventos `typing`, precismaos adicionar 'typing' aos eventos registrados inicialmente.

`register_initial_desired_events` em `core.py` é a função responsável por registar os eventos.

``` diff

# zulipterminal/core.py

    @async
    def register_initial_desired_events(self) -> None:
        event_types = [
            'message',
            'update_message',
            # ...
+           'typing',
            # ...
        ]
        response = self.client.register(event_types=event_types,
                                        apply_markdown=True)
```

Agora, para ver o tipo de dados que o servidor está enviando, nós vamos escrever a resposta do servidor em um arquivo.

Para isto, nós temporariamente adicionamos as seguintes linhas à função `poll_for_events` in `model.py`. A função usa 'long polling' (interrupção longa) para se manter em contato com o servidor, e continuamente recebe eventos do servidor.

``` diff

# zulipterminal/model.py

            for event in response['events']:
+               with open('type', 'a') as f:
+                   f.write(str(event) + "\n")
                last_event_id = max(last_event_id, int(event['id']))
```

Agora, execute o zulip terminal e abra o aplicativo web em uma conta diferente. Começe a escrever a mensagem para sua conta do terminal no aplicativo web, e você vai começar a receber 2 tipos de eventos:

**Start**
```
{
  'type': 'typing',
  'op': 'start',
  'sender': {
    'user_id': 4,
    'email': 'hamlet@zulip.com'
  },
  'recipients': [{
    'user_id': 2,
    'email': 'ZOE@zulip.com'
  }, {
    'user_id': 4,
    'email': 'hamlet@zulip.com'
  }, {
    'user_id': 5,
    'email': 'iago@zulip.com'
  }],
  'id': 0
}
```


**Stop**
```
{
  'type': 'typing',
  'op': 'stop',
  'sender': {
    'user_id': 4,
    'email': 'hamlet@zulip.com'
  },
  'recipients': [{
    'user_id': 2,
    'email': 'ZOE@zulip.com'
  }, {
    'user_id': 4,
    'email': 'hamlet@zulip.com'
  }, {
    'user_id': 5,
    'email': 'iago@zulip.com'
  }],
  'id': 1
}
```
Você pode ver estes eventos no arquivo `type` no seu diretório principal `zulip-terminal`

Agora para mostrar se o usuário está digitando na interface, precisamos garantir que os seguintes prerequisitos estão satisfeitos:
* O `op` é `start`.
* O usuário selecionou uma mensagem privada com um usuário.
* O `user_id` da pessoa está presente nos recipientes da mensagem privada.

Se todas as condições acima estão satisfeitas, nós podemos proceguir com a atualização do footer, e exibir `X is typing` até que nós recebamos um evento `stop`de digitação.

Para checar as condições acima, criamos uma função em `ui.py`:

```python

    def handle_typing_event(self, event: Dict['str', Any]) -> None:
        # If the user is in pm narrow with the person typing
        if len(self.model.narrow) == 1 and\
                self.model.narrow[0][0] == 'pm_with' and\
                event['sender']['email'] in self.model.narrow[0][1].split(','):
            if event['op'] == 'start':
                user = self.model.user_dict[event['sender']['email']]
                self._w.footer.set_text([
                    ' ',
                    ('code', user['full_name']),
                    ' is typing...'
                ])
                self.controller.update_screen()
            elif event['op'] == 'stop':
                self._w.footer.set_text(self.get_random_help())
                self.controller.update_screen()
```
Se as condições forem safisteitas, nós exibimos `x is typing` se o `op` está setado como `start`, e exibir uma mensagem de ajuda se o `op` é `stop`.

Existem duas etapas para atualizar um widget no urwid:
* Modificar o widget
* Atualizar a tela

Esta linha de código,
```python
self._w.footer.set_text([
                    ' ',
                    ('code', user['full_name']),
                    ' is typing...'
                ])
```
muda o texto do footer, e essa
```python
self.controller.update_screen()
```
atualiza a tela para exibir as mudanças. Com isso, terminamos de implementar a feature de digitando.
updates the screen to display the changes. This fully implements the typing feature.

### Escrevendo testes

Agora, atualizamos os testes para `register_initial_desired_events`, adicionando `typing` para os tipos de eventos.

```diff
# tests/core/test_core.py

        event_types = [
            'message',
            'update_message',
            'reaction',
+           'typing',
        ]
        controller.client.register.assert_called_once_with(
                                   event_types=event_types,
                                   apply_markdown=True)
```

A função `test_handle_typing_event` em `test_ui.py` implementa testes para o `handle_typing_event`. Por favor, leia-o para compreender como escrever testes para uma nova função no zulip terminal.

Obrigado por ler o tutorial. Até o pull request! :smiley:
