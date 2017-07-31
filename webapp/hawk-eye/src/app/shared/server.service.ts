import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';
import 'rxjs/add/operator/map';

@Injectable()
export class ServerService {

	public url = 'http://localhost:5002'

	constructor (
    private http: Http
  ) {}

  getSRPL() {
    return this.http.get(this.url + '/faces/srpl')
    .map((res:Response) => res.json());
  }

}