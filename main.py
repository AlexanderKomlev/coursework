import json
import requests
from tqdm import tqdm


class APIVKClient:
    API_BASE_URL = 'https://api.vk.com/method'

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id

    def _build_url(self, api_method):
        return f'{self.API_BASE_URL}/{api_method}'

    def _get_common_params(self):
        return {
            'access_token': self.token,
            'v': '5.131'
        }

# Загрузка фотографий профиля
    def get_profile_photos_list(self):
        params = self._get_common_params()
        params.update({
            'owner_id': self.user_id,
            'album_id': 'profile',
            'extended': 1
        })
        response = requests.get(self._build_url('photos.get'), params=params)
        return response.json()

# Загрузка фотографий со стены
    def get_wall_photos_list(self):
        params = self._get_common_params()
        params.update({
            'owner_id': self.user_id,
            'album_id': 'wall',
            'extended': 1
        })
        response = requests.get(self._build_url('photos.get'), params=params)
        return response.json()

# Загрузка сохраненных фотографий
# Необходим соответствующий токен доступа
    def get_saved_photos_list(self):
        params = self._get_common_params()
        params.update({
            'owner_id': self.user_id,
            'album_id': 'saved',
            'extended': 1
        })
        response = requests.get(self._build_url('photos.get'), params=params)
        return response.json()


class UploadPhotoToYandexDisk:
    base_url = 'https://cloud-api.yandex.net'

    def __init__(self, yandex_token):
        self.yandex_token = yandex_token
        self.headers = {'Authorization': self.yandex_token}
        self.json_dict = {'files': []}
        self.count_photo = 0

    def _folder_creation(self):
        params = {'path': 'Profile photos'}
        requests.put(f'{self.base_url}/v1/disk/resources',
                     params=params,
                     headers=self.headers)

    def _get_url_to_upload(self, file_name):
        params = {'path': f'Profile photos/{file_name}'}
        response = requests.get(f'{self.base_url}/v1/disk/resources/upload',
                                params=params,
                                headers=self.headers)
        return response.json()['href']

    def uploading_photo(self, json_list, count_photo=5):
        self._folder_creation()
        photos = json_list.get('response', {}).get('items', [])
        photos.sort(key=lambda dictionary: dictionary['likes']['count'])
        like_count = -1
        date_photo = photos[0]['date']

        pbar = tqdm(photos[:count_photo], desc='Загрузка фотографий на Яндекс.Диск')
        for photo in pbar:
            if photo['likes']['count'] == like_count:
                self.json_dict['files'].append({"file_name": f"{photo['likes']['count']}{photo['date']}.jpg"})
                if self.json_dict['files'] != []:
                    self.json_dict['files'][self.count_photo - 1]["file_name"] = f'{like_count}{date_photo}.jpg'
            else:
                self.json_dict['files'].append({"file_name": f"{photo['likes']['count']}.jpg"})
            self.json_dict['files'][self.count_photo].update({"size": photo['sizes'][-1]['type']})
            like_count = photo['likes']['count']
            date_photo = photo['date']
            response = requests.get(photo['sizes'][-1]['url'])
            try:
                upload_url = self._get_url_to_upload(self.json_dict['files'][self.count_photo]['file_name'])
            except (requests.exceptions.MissingSchema, KeyError):
                self.json_dict['files'][self.count_photo]['file_name'] = f"{photo['likes']['count']}{photo['date']}.jpg"
                upload_url = self._get_url_to_upload(self.json_dict['files'][self.count_photo]['file_name'])
            if 200 <= response.status_code < 300:
                requests.put(upload_url, files={'file': response.content})
            else:
                print('File upload error')
            self.count_photo += 1


if __name__ == '__main__':
    access_token = ''

    user_id = input('Введите id пользователя')
    yandex_oauth_token = input('Введите токен с полигона ЯД')

    client = APIVKClient(access_token, user_id)
    uploading = UploadPhotoToYandexDisk(yandex_oauth_token)
    uploading.uploading_photo(client.get_profile_photos_list(), 1)
    uploading.uploading_photo(client.get_wall_photos_list(), 2)
    uploading.uploading_photo(client.get_saved_photos_list(), 2)

    with open('result.json', 'w') as file:
        json.dump(uploading.json_dict, file, ensure_ascii=False, indent=2)
