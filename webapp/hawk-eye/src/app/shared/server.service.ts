import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import 'rxjs/add/operator/map';

@Injectable()
export class ServerService {

	public url = 'http://172.17.0.2:8000'

	constructor (
    private http: Http
  ) {}

  getSRPL() {
    return this.http.get(this.url + '/faces/srpl')
    .map((res:Response) => res.json());
  }

}
