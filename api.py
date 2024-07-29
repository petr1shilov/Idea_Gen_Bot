import re
from datetime import datetime
import requests
import uuid
import json
import config
import time
from openai import OpenAI

class IdeaGenAPI:

    def __init__(self, auth_giga=config.auth_giga, auth_gpt=config.auth_gpt):
        self.auth_giga = auth_giga
        self.auth_gpt = auth_gpt
        self.model = 'ChatGPT4'
        self.client = OpenAI(api_key=config.auth_gpt)
        self.response = None

    def set_model(self, new_model):
        self.model = new_model

    def parsing_agents(self, text_agent):
        request_text = re.split(r"\[.+\]", text_agent)
        request_text = request_text[1:]
        clean_request_text = [re.sub(r"[\n]", "", i) for i in request_text]
        request_name = re.findall(r"\[.+\]", text_agent)

        agents = {}
        for i in range(len(request_name)):
            agents[request_name[i]] = clean_request_text[i]
        return agents

    def check_auth_token(self):
        print(self.response)
        if (self.response is None) or (
            self.response.json()["expires_at"] <= time.time() * 1000
        ):
            response = self.get_token()
            self.response = response
        else:
            response = self.response
        return response

    def get_token(self, scope="GIGACHAT_API_PERS"):
        """
        Выполняет POST-запрос к эндпоинту, который выдает токен.

        Параметры:
        - auth_token (str): токен авторизации, необходимый для запроса.
        - scope (str): область действия запроса API. По умолчанию — «GIGACHAT_API_PERS».

        Возвращает:
        - ответ API, где токен и срок его "годности".
        """

        # Создадим идентификатор UUID (36 знаков)
        rq_uid = str(uuid.uuid4())

        # API URL
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        # Заголовки
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rq_uid,
            "Authorization": f"Basic {self.auth_giga}",
        }

        # Тело запроса
        payload = {"scope": scope}

        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            return response
        except requests.RequestException as e:
            print(f"Ошибка: {str(e)}")
            return -1

    def get_gigachat_completion(self, auth_token, conversation_history=None):
        """
        Отправляет POST-запрос к API чата для получения ответа от модели GigaChat в рамках диалога.

        Параметры:
        - auth_token (str): Токен для авторизации в API.
        - user_message (str): Сообщение от пользователя, для которого нужно получить ответ.
        - conversation_history (list): История диалога в виде списка сообщений (опционально).

        Возвращает:
        - response (requests.Response): Ответ от API.
        - conversation_history (list): Обновленная история диалога.
        """
        # URL API, к которому мы обращаемся
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

        # Подготовка данных запроса в формате JSON
        payload = json.dumps(
            {
                "model": "GigaChat-Pro",
                "messages": conversation_history,
                "temperature": 1,
                "top_p": 0.1,
                "n": 1,
                "stream": False,
                "max_tokens": 512,
                "repetition_penalty": 1,
                "update_interval": 0,
            }
        )
        # Заголовки запроса
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {auth_token}",
        }

        # Выполнение POST-запроса и возвращение ответа
        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            return response
        except requests.RequestException as e:
            # Обработка исключения в случае ошибки запроса
            print(f"Произошла ошибка: {str(e)}")
            return None

    def get_answer_giga(self, agents, theme, len_dialog: int):

        content = []
        count = 1
        total_tokens = 0

        response = self.check_auth_token()
        if response != -1:
            giga_token = response.json()["access_token"]

        agents = self.parsing_agents(agents)

        system_prompt = f'Представь что это брейншторм {len(agents)} людей на тему: {theme}.\n\n'
        for agent in agents:
            text = f'''Специалист номер {count} - Тебя зовут {agent}. Ты {agents[agent]} 
            Ты участвуешь в научном брейншторме на тему {theme} вместе с:
            {set(agents) - set([agent])}. 
            Все специалисты говорят по очереди.\n\n'''
    
            system_prompt += text
            count += 1

        conversation_history = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]
        for _ in range(len_dialog):
            for agent in agents:
                prompt = f"""
                Cейчас очередь {agent}.
                Дополни, покритикуй или предложи альтернативу обсуждаемым идеям на ответы предыдущего специалиста.
                Твой ответ должен быть 1-2 предложения. В каждом предожении примерно 7 слов.
                """
                conversation_history.append({"role": "user", "content": prompt})

                answer = self.get_gigachat_completion(giga_token, conversation_history)

                conversation_history.append(
                    {
                        "role": "assistant",
                        "content": answer.json()["choices"][0]["message"]["content"],
                    }
                )
                content.append(
                    {agent: answer.json()["choices"][0]["message"]["content"]}
                )
                total_tokens += int(answer.json()['usage']['total_tokens'])
                # print(conversation_history)
                # print(answer.json()['choices'][0]['message']['content'])

        takeoffs_system_prompt = f"""Ты опытный ученый, который подводит итог научного диспута на тему:{theme}. 
                    В диалоге участвуют: {agents}. 
                    Текст диалога: 
                        начало диалога: {content} 
                        конец диалога. 
                    Сформируй нумерованный список ценных идей, озвученых в диалоге, приведи не менее 1 идеи."""
        conversation_history_takeoffs = [
            {"role": "system", "content": takeoffs_system_prompt}
        ]
        answer_total = self.get_gigachat_completion(
            giga_token, conversation_history_takeoffs
        )

        total_tokens += int(answer_total.json()['usage']['total_tokens'])
        print(f'всего было потрачего --> {total_tokens} токенов на {len(agents) * 2 + 1} реплик')
        print(conversation_history)

        return content, answer_total.json()["choices"][0]["message"]["content"]
    
    def get_gpt4_completion(self, conversation_history):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history
            )
        return response
    
    def get_answer_gpt4(self, agents, theme, len_dialog: int):

        content = []
        count = 1
        total_tokens = 0
        first_messege = True
        total_prompt_tokens = 0
        total_completion_tokens = 0

        agents = self.parsing_agents(agents)

        system_prompt = f'Представь что это брейншторм {len(agents)} людей на тему: {theme}.\n\n'
        for agent in agents:
            text = f'''Специалист номер {count} - Тебя зовут {agent}. Ты {agents[agent]} 
            Ты участвуешь в научном брейншторме на тему {theme} вместе с:
            {set(agents) - set([agent])}. 
            Все специалисты говорят по очереди.\n\n'''
    
            system_prompt += text
            count += 1

        conversation_history = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]
        for _ in range(len_dialog):
            for agent in agents:
                if first_messege:
                    prompt = f"""
                    Cейчас очередь {agent}.
                    Ты говоришь первым, поэтому не забудь поздароваться.
                    Начни диалог по теме.
                    Твой ответ должен быть 1-2 предложения. В каждом предожении примерно 7 слов. Скажи только саму реплику.
                    """
                    first_messege = False
                else:
                    prompt = f"""
                    Cейчас очередь {agent}.
                    Дополни, покритикуй или предложи альтернативу обсуждаемым идеям на ответы предыдущего специалиста.
                    Твой ответ должен быть 1-2 предложения. В каждом предожении примерно 7 слов. Скажи только саму реплику, не начинай с имени {agent} и не надо здороватся.
                    """
                conversation_history.append({"role": "user", "content": prompt})

                answer = self.get_gpt4_completion(conversation_history)

                conversation_history.append(
                    {
                        "role": "assistant",
                        "content": answer.choices[0].message.content,
                    }
                )
                content.append({agent: answer.choices[0].message.content})
                total_prompt_tokens += int(answer.usage.prompt_tokens)
                total_completion_tokens += int(answer.usage.completion_tokens)
                # print(conversation_history)
                # print(answer.json()['choices'][0]['message']['content'])

        takeoffs_system_prompt = f"""Ты опытный ученый, который подводит итог научного диспута на тему:{theme}. 
                    В диалоге участвуют: {agents}. 
                    Текст диалога: 
                        начало диалога: {content} 
                        конец диалога. 
                    Сформируй нумерованный список ценных идей, озвученых в диалоге, приведи не менее 1 идеи.
                    Не надо упоминать участников диалога в своем ответе"""
        conversation_history_takeoffs = [
            {"role": "system", "content": takeoffs_system_prompt}
        ]
        answer_total = self.get_gpt4_completion(conversation_history_takeoffs)

        total_prompt_tokens += int(answer_total.usage.prompt_tokens)
        total_completion_tokens += int(answer_total.usage.completion_tokens)

        print((f'всего было потрачено --> {total_prompt_tokens + total_completion_tokens} токенов\n'
               f'на вход было потрачено --> {total_prompt_tokens}токенов\n' 
               f'на ответ было потрачено --> {total_completion_tokens}токенов\n' 
               f' на {len(agents) * len_dialog + 1} реплик'))
        # print(conversation_history)

        return content, answer_total.choices[0].message.content
    
    def get_answer(self, agents, theme, len_dialog: int):
        if self.model == 'ChatGPT4':
            return self.get_answer_gpt4(agents, theme, len_dialog)
        elif self.model == 'GigaChat':
            return self.get_answer_giga(agents, theme, len_dialog)